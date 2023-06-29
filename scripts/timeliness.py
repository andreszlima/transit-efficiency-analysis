import os
import psycopg2
import numpy as np
from scipy import stats
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def calculate_and_store_statistics():
    conn = psycopg2.connect(
        database=os.getenv("LOCAL_DB_NAME"),
        user=os.getenv("LOCAL_DB_USERNAME"),
        password=os.getenv("LOCAL_DB_PASSWORD"),
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    # Delete old data
    cur.execute("DELETE FROM route_stats;")

    # Get unique routes
    cur.execute("SELECT DISTINCT route_long_name FROM trip_updates_with_diffs;")
    routes = cur.fetchall()

    for route in routes:
        route = route[0]
        
        # Get the average value of arrival and departure time differences
        # If either is zero, use the non-zero one for that row.
        cur.execute(f"""
            SELECT AVG(
                CASE 
                    WHEN arrival_time_diff_in_seconds = 0 THEN departure_time_diff_in_seconds
                    WHEN departure_time_diff_in_seconds = 0 THEN arrival_time_diff_in_seconds
                    ELSE (arrival_time_diff_in_seconds + departure_time_diff_in_seconds) / 2.0
                END
            ) FROM trip_updates_with_diffs WHERE route_long_name = '{route}';
        """)
        average_delay = cur.fetchone()[0]

        # Get the mode of arrival and departure time differences
        cur.execute(f"""
            SELECT 
                CASE 
                    WHEN arrival_time_diff_in_seconds = 0 THEN departure_time_diff_in_seconds
                    WHEN departure_time_diff_in_seconds = 0 THEN arrival_time_diff_in_seconds
                    ELSE (arrival_time_diff_in_seconds + departure_time_diff_in_seconds) / 2.0
                END as delay 
            FROM trip_updates_with_diffs WHERE route_long_name = '{route}';
        """)
        delays = cur.fetchall()
        delays = np.array(delays)

        # Calculate standard deviation
        standard_deviation = np.std(delays)

        # Find most delayed and most early
        most_delayed = np.max(delays)
        most_early = np.min(delays)

        # Insert the stats into the table
        cur.execute(f"INSERT INTO route_stats (route_long_name, average_delay, standard_deviation, most_delayed, most_early) VALUES ('{route}', {average_delay}, {standard_deviation}, {most_delayed}, {most_early});")

    conn.commit()
    cur.close()
    conn.close()

    print('Route stats table populated!')

if __name__ == "__main__":
    calculate_and_store_statistics()
