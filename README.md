# Sudbury Transit Efficiency Analysis

![People leaving bus](public/canada%20bus.png?raw=true "Sudbury Transit Efficiency Analysis")

## Project Description
This project aims to analyze the efficiency and effectiveness of Sudbury's bus service. Leveraging publicly available data, the analysis is structured around three main objectives: 

1. **Bus Timeliness:** Analysis of scheduled versus actual bus arrival times.
2. **Route Efficiency:** Evaluation of the distribution of bus stops and service frequency across different routes.
3. **Peak Hour Analysis:** Identification of the busiest hours for the Sudbury bus transit system.

## Data Source
The data used in this project is sourced from the [Sudbury's open data Portal](http://sudbury.tmix.se/). This dataset provides detailed route and schedule information for all surface route operations, contained within General Transit Feed Specification (GTFS) files. GTFS data is split into two categories: historical and real-time data. 

Historical data, which is stored in `gtfs_data` table, provides general information about transit agencies, routes, stops, and scheduled service. Real-time data, on the other hand, is stored in `trip_updates` table and provides live updates about the actual position of buses and their predicted arrival times. By comparing scheduled and actual arrival times, we aim to analyze the timeliness and efficiency of Sudbury's bus service. 

## Tools and Technologies
* Python for data gathering, data cleaning, and analysis. Key libraries used include Pandas for data manipulation, requests for data downloading, and SQLAlchemy for database connection.
* PostgreSQL for data storage and management. Database queries are written in SQL for extracting insights from the data.
* Future work may include using Apache Airflow to automate and schedule data pipelines, and creating dashboards for data visualization.

## Setup & Execution

1. **Environment Setup:**
    The project uses environment variables for configuration. These can be set manually, but for ease of use, it's recommended to store them in an `.env` file. The python scripts will search for this file inside `scripts` folder. This file should not be committed to version control.

    Here's a sample `.env` file with all required variables:

    ```dotenv
    # Remote database username
    REMOTE_DB_USERNAME=<Your Remote DB Username>
    # Remote database password
    REMOTE_DB_PASSWORD=<Your Remote DB Password>
    # Remote database connection string. Replace 'localhost' with your DB host and 'transit_data' with your DB name
    REMOTE_DB_URL=postgresql://${REMOTE_DB_USERNAME}:${REMOTE_DB_PASSWORD}@localhost:5432/transit_data
    # Table name of realtime data
    REALTIME_TABLE=trip_updates
    # Table name of historical data
    HISTORICAL_TABLE=gtfs_data
    # Name of the remote database
    REMOTE_DB_NAME=transit_data
    # Name of the local database
    LOCAL_DB_NAME=transit_data
    # Local database username
    LOCAL_DB_USERNAME=<Your Local DB Username>
    # Local database password
    LOCAL_DB_PASSWORD=<Your Local DB Password>
    # Local database connection string. Replace 'localhost' with your DB host and 'transit_data' with your DB name
    LOCAL_DB_URL=postgresql://${LOCAL_DB_USERNAME}:${LOCAL_DB_PASSWORD}@localhost:5432/transit_data
    # VPS username
    VPS_USERNAME=<Your VPS Username>
    # VPS server IP
    VPS_SERVER_IP=<Your VPS Server IP>
    # Path to the csv file in the local machine
    LOCAL_CSV_FILE_PATH=<Path to your local csv file. it is erased after updating the table>
    # Path to your private key file
    PRIVATE_KEY_PATH=<Path to your private key file>
    ```

    Be sure to replace all `<Your ...>` placeholders with your actual data.


2. **Database Setup:**
    You need to create two tables in your PostgreSQL database: `gtfs_data` for the historical data and `trip_updates` for the realtime data.

    The required SQL commands for creating these tables are as follows:

    ```sql
    CREATE TABLE IF NOT EXISTS public.gtfs_data
    (
        trip_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
        start_date date NOT NULL,
        stop_sequence integer NOT NULL,
        stop_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
        route_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
        stop_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
        route_long_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
        arrival_time time without time zone,
        departure_time time without time zone,
        CONSTRAINT gtfs_data_pkey PRIMARY KEY (trip_id, start_date, stop_sequence, stop_id, route_id, stop_name, route_long_name)
    )
    ```

    ```sql
    CREATE TABLE IF NOT EXISTS public.trip_updates
    (
        trip_id text COLLATE pg_catalog."default" NOT NULL,
        start_date date NOT NULL,
        stop_sequence integer NOT NULL,
        stop_id text COLLATE pg_catalog."default" NOT NULL,
        departure_time timestamp with time zone NOT NULL DEFAULT '1970-01-01 02:00:00-03'::timestamp with time zone,
        arrival_time timestamp with time zone NOT NULL DEFAULT '1970-01-01 02:00:00-03'::timestamp with time zone,
        file_source timestamp with time zone NOT NULL,
        CONSTRAINT trip_updates_pkey PRIMARY KEY (trip_id, start_date, stop_sequence, stop_id, departure_time, arrival_time)
    )
    ```

3. **Execution:**
    The `realtime_extractor.py` script is executed on a regular basis on a remote server. This script pulls data from the GTFS real-time feed and stores it in the `trip_updates` table. The `historical_extractor.py` script, on the other hand, should be run manually as needed to pull and store historical data in the `gtfs_data` table.

    You can set the `realtime_extractor.py` script to run as a cron job on your remote server. To make the script run every 3 minutes, edit the crontab file with `crontab -e` and add the following line:

    ```bash
    */3 * * * * /usr/bin/python3 /path/to/realtime_extractor.py
    ```
    
    Be sure to replace `/path/to/realtime_extractor.py` with the actual path to the Python script on your server.

    If you want to get the most recent realtime data, you can use the included shell script. To do this, make sure the script is executable by running `chmod +x get_realtime.sh`.


## Findings
This section will be updated as we progress with the analysis and gather findings.

## Visualizations
Visualizations to complement the findings will be added in future updates.

## License
This project is licensed under the terms of the [MIT License](LICENSE.md).
