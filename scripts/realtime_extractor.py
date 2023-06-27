import os
import pandas as pd
import pytz
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib import gtfs_realtime_pb2
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# URL to download the data
url = "https://sudbury.tmix.se/gtfs-realtime/tripupdates.pb"

# Database connection string
db_string = os.getenv("REMOTE_DB_URL")

# The table name can be replaced
table_name = os.getenv("REALTIME_TABLE")

def parse_pb_data(data):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)

    parsed_data = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_id = entity.trip_update.trip.trip_id
            for update in entity.trip_update.stop_time_update:
                if update.HasField('departure'):
                    departure_time = pd.to_datetime(update.departure.time, unit='s', utc=True) if update.departure.time != 0 else pd.Timestamp('1970-01-01', tz='UTC')
                else:
                    departure_time = pd.Timestamp('1970-01-01', tz='UTC')
                if update.HasField('arrival'):
                    arrival_time = pd.to_datetime(update.arrival.time, unit='s', utc=True) if update.arrival.time != 0 else pd.Timestamp('1970-01-01', tz='UTC')
                else:
                    arrival_time = pd.Timestamp('1970-01-01', tz='UTC')

                parsed_data.append({
                    'trip_id': trip_id,
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

    # Save individual snapshot
    timestamp = pd.Timestamp.utcnow().floor('s')
    print(f'Inserting data with source {timestamp}...')
    df['file_source'] = timestamp

    # Insert data into the database
    try:
        with engine.connect() as conn:
            for _, row in df.iterrows():
                # Check if arrival or departure time is older than the current time
                if row['arrival_time'] < timestamp or row['departure_time'] < timestamp:
                    insert_query = text(f"""
                        INSERT INTO {table_name} (trip_id, stop_sequence, stop_id, departure_time, arrival_time, file_source)
                        VALUES (:trip_id, :stop_sequence, :stop_id, :departure_time, :arrival_time, :file_source)
                        ON CONFLICT (trip_id, stop_sequence, stop_id, departure_time, arrival_time) 
                        DO NOTHING
                    """)
                    conn.execute(insert_query, row.to_dict())
            conn.commit()
        print('Data inserted.')
    except Exception as e:
        print(f"Error occurred while inserting data into the database: {e}")


if __name__ == "__main__":
    main()
