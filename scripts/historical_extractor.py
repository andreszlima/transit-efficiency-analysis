import os
import requests
import pandas as pd
import zipfile
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# URL to download the data
url = "https://sudbury.tmix.se/gtfs/gtfs.zip"

# Database connection string
db_string = os.getenv("DB_URL")


def parse_date_and_time(date_str, time_str):
    hour, minute, second = map(int, time_str.split(':'))
    date = pd.to_datetime(date_str, format="%Y%m%d")
    if hour >= 24:
        hour -= 24
        date += pd.Timedelta(days=1)
    timestamp = pd.Timestamp(year=date.year, month=date.month, day=date.day, hour=hour, minute=minute, second=second)
    return timestamp.tz_localize('UTC').tz_convert('America/Toronto')


def main():
    # Create engine
    engine = create_engine(db_string)

    # Download data
    print('Downloading data...')
    response = requests.get(url)
    print('Download complete.')

    # Extract and parse data
    print('Extracting and parsing data...')
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        with zf.open('stop_times.txt') as f:
            stop_times_df = pd.read_csv(f)

        with zf.open('trips.txt') as f:
            trips_df = pd.read_csv(f)

        with zf.open('calendar_dates.txt') as f:
            calendar_dates_df = pd.read_csv(f)

        with zf.open('stops.txt') as f:
            stops_df = pd.read_csv(f)

        with zf.open('routes.txt') as f:
            routes_df = pd.read_csv(f)

    # Merge dataframes
    df = (stop_times_df
          .merge(trips_df, on='trip_id')
          .merge(calendar_dates_df, on='service_id')
          .merge(stops_df, on='stop_id')
          .merge(routes_df, on='route_id'))

    # Convert arrival_time and departure_time to timestamp
    df['arrival_time'] = df.apply(lambda row: parse_date_and_time(str(row['date']), row['arrival_time']), axis=1)
    df['departure_time'] = df.apply(lambda row: parse_date_and_time(str(row['date']), row['departure_time']), axis=1)

    # Select columns
    df = df[['trip_id', 'stop_sequence', 'stop_id', 'route_id', 'stop_name', 'route_long_name', 'arrival_time', 'departure_time']]
    print('Data parsed.')

    # Insert data into the database
    print('Inserting data into the database...')
    df.to_sql('gtfs_data', con=engine, if_exists='replace', index=False)
    print('Data inserted.')


if __name__ == "__main__":
    main()
