import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta
import pytz

# Load .env file
load_dotenv()

def populate_table():

    # Get current datetime in UTC
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    conn = psycopg2.connect(
        database=os.getenv("LOCAL_DB_NAME"),
        user=os.getenv("LOCAL_DB_USERNAME"),
        password=os.getenv("LOCAL_DB_PASSWORD"),
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    # Delete old data
    cur.execute("DELETE FROM trip_updates_with_diffs;")

    # Populate the table with the new data
    query = """
    INSERT INTO trip_updates_with_diffs
    SELECT 
        tu.trip_id, 
        tu.start_date, 
        tu.stop_sequence, 
        tu.stop_id::bigint,
        gd.route_id, 
        gd.stop_name, 
        gd.route_long_name, 
        CASE
            WHEN EXTRACT(EPOCH FROM tu.arrival_time) = 0 THEN NULL
            ELSE tu.arrival_time
        END AS actual_arrival_time, 
        gd.arrival_time AS scheduled_arrival_time,
        CASE
            WHEN EXTRACT(EPOCH FROM tu.arrival_time) = 0 THEN 0
            ELSE EXTRACT(EPOCH FROM (tu.arrival_time - gd.arrival_time)) / 60
        END AS arrival_time_diff_in_minutes,
        CASE
            WHEN EXTRACT(EPOCH FROM tu.departure_time) = 0 THEN NULL
            ELSE tu.departure_time
        END AS actual_departure_time,
        gd.departure_time AS scheduled_departure_time,
        CASE
            WHEN EXTRACT(EPOCH FROM tu.departure_time) = 0 THEN 0
            ELSE EXTRACT(EPOCH FROM (tu.departure_time - gd.departure_time)) / 60
        END AS departure_time_diff_in_minutes,
        CASE
            WHEN (EXTRACT(EPOCH FROM tu.arrival_time) <> 0 AND EXTRACT(EPOCH FROM tu.departure_time) <> 0) THEN
                (EXTRACT(EPOCH FROM (tu.arrival_time - gd.arrival_time)) + EXTRACT(EPOCH FROM (tu.departure_time - gd.departure_time))) / 120
            WHEN (EXTRACT(EPOCH FROM tu.arrival_time) = 0 AND EXTRACT(EPOCH FROM tu.departure_time) <> 0) THEN
                EXTRACT(EPOCH FROM (tu.departure_time - gd.departure_time)) / 60
            WHEN (EXTRACT(EPOCH FROM tu.arrival_time) <> 0 AND EXTRACT(EPOCH FROM tu.departure_time) = 0) THEN
                EXTRACT(EPOCH FROM (tu.arrival_time - gd.arrival_time)) / 60
            ELSE
                NULL
        END AS average_diff_in_minutes,
        tu.weather_group,
        tu.weather_description,
        tu.temperature,
        CASE
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 0 THEN 'Sunday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 1 THEN 'Monday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 2 THEN 'Tuesday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 3 THEN 'Wednesday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 4 THEN 'Thursday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 5 THEN 'Friday'
            WHEN EXTRACT(DOW FROM gd.arrival_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Toronto') = 6 THEN 'Saturday'
        END AS day_type,
        DATE_PART('hour', gd.arrival_time AT TIME ZONE 'America/Toronto') AS sudbury_hour_of_day,
        gd.geo_coordinates,
        tu.created_at,
        tu.updated_at
    FROM 
        """ + os.getenv("REALTIME_TABLE") + """ AS tu
    JOIN """ + os.getenv("HISTORICAL_TABLE") + """ AS gd
    ON tu.trip_id = gd.trip_id 
        AND tu.start_date = gd.start_date 
        AND tu.stop_sequence = gd.stop_sequence 
        AND tu.stop_id::bigint = gd.stop_id 
    WHERE 
        NOT (
            (EXTRACT(EPOCH FROM tu.arrival_time) = 0 AND EXTRACT(EPOCH FROM gd.arrival_time) <= 1000 * 60) AND
            (EXTRACT(EPOCH FROM tu.departure_time) = 0 AND EXTRACT(EPOCH FROM gd.departure_time) <= 1000 * 60)
        )
    ORDER BY tu.trip_id ASC, tu.stop_sequence ASC, tu.start_date ASC;
    """

    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

    print('Diff times table populated!')
    print('Current Datetime:', now)

if __name__ == "__main__":
    populate_table()