import os
from dotenv import load_dotenv
import psycopg2

# Load .env file
load_dotenv()

def populate_table():
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
        adjusted_trip_updates.trip_id, 
        adjusted_trip_updates.start_date, 
        adjusted_trip_updates.stop_sequence, 
        adjusted_trip_updates.stop_id::bigint,  
        adjusted_trip_updates.actual_arrival_time, 
        adjusted_trip_updates.actual_departure_time, 
        adjusted_trip_updates.file_source, 
        gtfs_data.route_id, 
        gtfs_data.stop_name, 
        gtfs_data.route_long_name, 
        gtfs_data.arrival_time AS scheduled_arrival_time, 
        gtfs_data.departure_time AS scheduled_departure_time,
        EXTRACT(EPOCH FROM (adjusted_trip_updates.actual_arrival_time - gtfs_data.arrival_time)) AS arrival_time_diff_in_seconds,
        EXTRACT(EPOCH FROM (adjusted_trip_updates.actual_departure_time - gtfs_data.departure_time)) AS departure_time_diff_in_seconds,
        CASE
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 0 THEN 'Sunday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 1 THEN 'Monday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 2 THEN 'Tuesday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 3 THEN 'Wednesday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 4 THEN 'Thursday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 5 THEN 'Friday'
            WHEN EXTRACT(DOW FROM adjusted_trip_updates.actual_arrival_time) = 6 THEN 'Saturday'
        END AS day_type,
        CASE
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 6 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 9 THEN 'Morning rush hour (6AM to 9AM)'
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 9 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 11 THEN 'Mid morning (9AM to 11AM)'
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 11 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 13 THEN 'Midday (11AM to 01PM)'
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 13 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 16 THEN 'Afternoon (01PM to 04PM)'
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 16 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 19 THEN 'Afternoon rush hour (04PM to 07PM)'
            WHEN DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') >= 19 AND DATE_PART('hour', adjusted_trip_updates.actual_arrival_time AT TIME ZONE 'America/Toronto') < 22 THEN 'Evening (07PM to 10PM)'
            ELSE 'Night (10PM to 6AM)'
        END AS time_of_day,
        gtfs_data.geo_coordinates
    FROM 
    (
        SELECT 
            distinct_trip_updates.trip_id, 
            distinct_trip_updates.start_date, 
            distinct_trip_updates.stop_sequence, 
            distinct_trip_updates.stop_id, 
            CASE 
                WHEN ABS(EXTRACT(EPOCH FROM (distinct_trip_updates.arrival_time - gtfs_data.arrival_time))) > 1000000000 THEN gtfs_data.arrival_time
                ELSE distinct_trip_updates.arrival_time 
            END AS actual_arrival_time,
            CASE 
                WHEN ABS(EXTRACT(EPOCH FROM (distinct_trip_updates.departure_time - gtfs_data.departure_time))) > 1000000000 THEN gtfs_data.departure_time
                ELSE distinct_trip_updates.departure_time 
            END AS actual_departure_time,
            distinct_trip_updates.file_source 
        FROM 
        (
            SELECT DISTINCT ON (trip_id, start_date, stop_sequence, stop_id) *
            FROM """ + os.getenv("REALTIME_TABLE") + """
            ORDER BY trip_id, start_date, stop_sequence, stop_id, file_source DESC
        ) AS distinct_trip_updates
        JOIN """ + os.getenv("HISTORICAL_TABLE") + """ 
        ON distinct_trip_updates.trip_id = gtfs_data.trip_id 
        AND distinct_trip_updates.start_date = gtfs_data.start_date 
        AND distinct_trip_updates.stop_sequence = gtfs_data.stop_sequence 
        AND distinct_trip_updates.stop_id::bigint = gtfs_data.stop_id 
    ) AS adjusted_trip_updates
    JOIN """ + os.getenv("HISTORICAL_TABLE") + """ 
    ON adjusted_trip_updates.trip_id = gtfs_data.trip_id 
    AND adjusted_trip_updates.start_date = gtfs_data.start_date 
    AND adjusted_trip_updates.stop_sequence = gtfs_data.stop_sequence 
    AND adjusted_trip_updates.stop_id::bigint = gtfs_data.stop_id
    WHERE 
        NOT (
            EXTRACT(EPOCH FROM (adjusted_trip_updates.actual_arrival_time - gtfs_data.arrival_time)) = 0 AND
            EXTRACT(EPOCH FROM (adjusted_trip_updates.actual_departure_time - gtfs_data.departure_time)) = 0
        )
    ORDER BY adjusted_trip_updates.trip_id ASC, stop_sequence ASC, start_date ASC;
    """

    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

    print('Diff times table populated!')

if __name__ == "__main__":
    populate_table()
