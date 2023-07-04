import os
import requests
import pandas as pd
import zipfile
import io
import pytz
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# URL to download the data
url = "https://sudbury.tmix.se/gtfs/gtfs.zip"

# Database connection string
db_string = os.getenv("LOCAL_DB_URL")

# The table name can be replaced
table_name = os.getenv("HISTORICAL_TABLE")

# Chunk size
chunk_size = 5000  # Adjust as necessary depending on your server's resources

def parse_date_and_time_vectorized(dates, times):
    sudbury_tz = pytz.timezone('America/Toronto')  # Sudbury is in the Toronto time zone
    hours, minutes, seconds = zip(*[map(int, time.split(':')) for time in times])
    hours = pd.Series(hours)
    dates = pd.to_datetime(dates, format="%Y%m%d")
    dates += pd.to_timedelta((hours // 24).astype(int), unit='d')
    hours %= 24
    timestamps = pd.to_datetime(dates.astype(str) + ' ' + hours.astype(str) + ':' + pd.Series(minutes).astype(str) + ':' + pd.Series(seconds).astype(str))
    # Convert to Sudbury's time zone first
    timestamps = timestamps.dt.tz_localize(sudbury_tz)
    # Then convert to UTC
    return timestamps.dt.tz_convert('UTC')

def main():
    # Create engine and session
    engine = create_engine(db_string)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Download data
    print('Downloading data...')
    response = requests.get(url)
    print('Download complete.')

    # Extract and parse data
    print('Extracting and parsing data...')
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        # Read in dataframes
        stop_times_df = pd.read_csv(zf.open('stop_times.txt'), chunksize=chunk_size)
        trips_df = pd.read_csv(zf.open('trips.txt'))
        calendar_dates_df = pd.read_csv(zf.open('calendar_dates.txt'))
        stops_df = pd.read_csv(zf.open('stops.txt'))
        routes_df = pd.read_csv(zf.open('routes.txt'))

        count = 0
        for chunk in stop_times_df:
            # Merge dataframes
            df = (chunk
                .merge(trips_df, on='trip_id')
                .merge(calendar_dates_df, on='service_id')
                .merge(stops_df, on='stop_id')
                .merge(routes_df, on='route_id'))

            # Convert arrival_time and departure_time to timestamp
            df['arrival_time'] = parse_date_and_time_vectorized(df['date'].astype(str), df['arrival_time'])
            df['departure_time'] = parse_date_and_time_vectorized(df['date'].astype(str), df['departure_time'])

            # Convert start_date to a date
            df['date'] = pd.to_datetime(df['date'], format="%Y%m%d").dt.date
            df.rename(columns={'date': 'start_date'}, inplace=True)

            # Create a new column "geo_coordinates" combining latitude and longitude
            df['geo_coordinates'] = df['stop_lat'].astype(str) + ', ' + df['stop_lon'].astype(str)

            # Select columns
            df = df[['trip_id', 'start_date', 'stop_sequence', 'stop_id', 'route_id', 'stop_name', 'route_long_name', 'arrival_time', 'departure_time', 'geo_coordinates']]
            
            # Insert data into the database
            for row in df.itertuples(index=False):
                insert_query = text(f"""INSERT INTO {table_name} (trip_id, start_date, stop_sequence, stop_id, route_id, stop_name, route_long_name, arrival_time, departure_time, geo_coordinates) 
                                    VALUES (:trip_id, :start_date, :stop_sequence, :stop_id, :route_id, :stop_name, :route_long_name, :arrival_time, :departure_time, :geo_coordinates) 
                                    ON CONFLICT DO NOTHING""")
                session.execute(insert_query, dict(row._asdict()))
            
            # Print progress
            count += chunk_size
            print(f'{count} chunks have been processed and inserted.')

            # Commit the transaction
            session.commit()

    print('Data parsed and inserted.')
    session.close()

if __name__ == "__main__":
    main()