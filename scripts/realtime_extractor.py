import os
import pandas as pd
import requests
import json
import pytz
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib import gtfs_realtime_pb2
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# URL to download the data
url = "https://sudbury.tmix.se/gtfs-realtime/tripupdates.pb"

# OpenWeather API details
open_weather_api_key = os.getenv("OPEN_WEATHER_API_KEY")
open_weather_api_url = f"http://api.openweathermap.org/data/2.5/weather?q=Sudbury,ca&appid={open_weather_api_key}"

# Database connection string
db_string = os.getenv("REMOTE_DB_URL")

# The table name can be replaced
table_name = os.getenv("REALTIME_TABLE")

# Path to the file to store the time of last API call
last_api_call_file = Path("last_api_call.json")

def get_last_api_call():
    if last_api_call_file.is_file():
        with open(last_api_call_file, 'r') as f:
            return datetime.fromisoformat(json.load(f)['last_api_call'])
    else:
        return datetime.now() - timedelta(minutes=3)

def set_last_api_call(last_api_call):
    with open(last_api_call_file, 'w') as f:
        json.dump({'last_api_call': last_api_call.isoformat()}, f)

def get_weather_data():
    last_api_call = get_last_api_call()
    if datetime.now() - last_api_call < timedelta(minutes=2):
        return None
    last_api_call = datetime.now()
    set_last_api_call(last_api_call)
    try:
        print('Getting weather data...')
        weather_data = requests.get(open_weather_api_url).json()
        print('Got weather data.')
        weather_id = weather_data['weather'][0]['id']
        weather_description = weather_data['weather'][0]['description']
        temperature_k = weather_data['main']['temp']  # this is in Kelvin

        # convert to Celsius
        temperature_c = temperature_k - 273.15

        if 200 <= weather_id <= 299:
            weather_group = 'Thunderstorm'
        elif 300 <= weather_id <= 399:
            weather_group = 'Drizzle'
        elif 500 <= weather_id <= 599:
            weather_group = 'Rain'
        elif 600 <= weather_id <= 699:
            weather_group = 'Snow'
        elif 700 <= weather_id <= 799:
            weather_group = 'Atmosphere'
        elif weather_id == 800:
            weather_group = 'Clear'
        elif 800 <= weather_id <= 899:
            weather_group = 'Clouds'
        else:
            weather_group = 'Unknown'
        
        return {
            'weather_group': weather_group,
            'weather_description': weather_description,
            'temperature': temperature_c
        }

    except Exception as e:
        print(f"Error occurred while getting weather data: {e}")
        return None


def parse_pb_data(data):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)

    parsed_data = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_id = entity.trip_update.trip.trip_id
            start_date = entity.trip_update.trip.start_date
            for update in entity.trip_update.stop_time_update:
                departure_time = pd.to_datetime(update.departure.time, unit='s', utc=True) if update.HasField('departure') else None
                arrival_time = pd.to_datetime(update.arrival.time, unit='s', utc=True) if update.HasField('arrival') else None
                parsed_data.append({
                    'trip_id': trip_id,
                    'start_date': start_date,
                    'stop_sequence': update.stop_sequence,
                    'stop_id': update.stop_id,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                })

    return pd.DataFrame(parsed_data)



def main():
    # Create engine
    engine = create_engine(db_string)
    
    try:
        # Download data
        print('Downloading data...')
        response = requests.get(url)
        response.raise_for_status()
        print('Download complete.')
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while downloading data: {e}")
        return

    try:
        # Parse data
        print('Parsing data...')
        df = parse_pb_data(response.content)
        print('Parsing complete.')
    except Exception as e:
        print(f"Error occurred while parsing data: {e}")
        return

    # Get weather data
    weather_data = get_weather_data()

    # Get current datetime in UTC
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    # Replace 'NaT' with None
    df['arrival_time'].replace({pd.NaT: None}, inplace=True)
    df['departure_time'].replace({pd.NaT: None}, inplace=True)

    # Insert data into the database
    try:
        with engine.connect() as conn:
            for _, row in df.iterrows():
                if weather_data is not None:
                    row['weather_group'] = weather_data['weather_group']
                    row['weather_description'] = weather_data['weather_description']
                    row['temperature'] = weather_data['temperature']  # add temperature
                    insert_query = text(f"""
                        INSERT INTO {table_name} (trip_id, start_date, stop_sequence, stop_id, arrival_time, departure_time, weather_group, weather_description, temperature, created_at)
                        VALUES (:trip_id, :start_date, :stop_sequence, :stop_id, :arrival_time, :departure_time, :weather_group, :weather_description, :temperature, :created_at)
                        ON CONFLICT (trip_id, start_date, stop_sequence, stop_id) 
                        DO UPDATE SET 
                        arrival_time = EXCLUDED.arrival_time,
                        departure_time = EXCLUDED.departure_time,
                        weather_group = EXCLUDED.weather_group, 
                        weather_description = EXCLUDED.weather_description,
                        temperature = EXCLUDED.temperature,
                        updated_at = :updated_at
                        WHERE 
                        {table_name}.arrival_time != EXCLUDED.arrival_time OR
                        {table_name}.departure_time != EXCLUDED.departure_time""")
                else:
                    insert_query = text(f"""
                        INSERT INTO {table_name} (trip_id, start_date, stop_sequence, stop_id, arrival_time, departure_time, created_at)
                        VALUES (:trip_id, :start_date, :stop_sequence,:stop_id, :arrival_time, :departure_time, :created_at)
                        ON CONFLICT (trip_id, start_date, stop_sequence, stop_id) 
                        DO UPDATE SET 
                        arrival_time = EXCLUDED.arrival_time,
                        departure_time = EXCLUDED.departure_time,
                        updated_at = :updated_at
                        WHERE 
                        {table_name}.arrival_time != EXCLUDED.arrival_time OR
                        {table_name}.departure_time != EXCLUDED.departure_time""")

                # Create a Transaction object and execute the insert query
                with conn.begin():
                    conn.execute(insert_query, {**row.to_dict(), 'created_at': now, 'updated_at': now})
            print('Data inserted.')
            print('Current Datetime:', now)
    except Exception as e:
        print(f"Error occurred while inserting data into the database: {e}")





if __name__ == "__main__":
    main()
