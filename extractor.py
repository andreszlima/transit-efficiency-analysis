import os
import pandas as pd
import pytz
import requests
from pathlib import Path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib import gtfs_realtime_pb2

# URL to download the data
url = "https://sudbury.tmix.se/gtfs-realtime/tripupdates.pb"

def parse_pb_data(data):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)

    parsed_data = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_id = entity.trip_update.trip.trip_id
            for update in entity.trip_update.stop_time_update:
                parsed_data.append({
                    'trip_id': trip_id,
                    'stop_sequence': update.stop_sequence,
                    'stop_id': update.stop_id,
                    'arrival_time': pd.to_datetime(update.arrival.time, unit='s', utc=True).tz_convert('America/Toronto') if update.HasField('arrival') else None,
                    'departure_time': pd.to_datetime(update.departure.time, unit='s', utc=True).tz_convert('America/Toronto') if update.HasField('departure') else None,
                })

    return pd.DataFrame(parsed_data)

def main():
    root_dir = Path(__file__).parent.parent
    processed_dir = root_dir / 'data/processed'
    os.makedirs(processed_dir, exist_ok=True)

    # Download data
    print('Downloading data...')
    response = requests.get(url)
    response.raise_for_status()
    print('Download complete.')

    # Parse data
    print('Parsing data...')
    df = parse_pb_data(response.content)
    print('Parsing complete.')

    # Save individual snapshot
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    print(f'Saving individual snapshot as {timestamp}.csv...')
    df.to_csv(processed_dir / f'{timestamp}.csv', index=False)
    print('Snapshot saved.')

if __name__ == "__main__":
    main()