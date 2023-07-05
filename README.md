# Sudbury's Transit Efficiency Analysis

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
* Google Data Studio for data visualization and analysis. Data is stored in a PostgreSQL database and Google Data Studio could be used to connect to the database, but since my database is hosted locally, I export the data as .csv file and upload it to Google Data Studio.

## Setup & Execution

0. **Firewall and resources**

    Make sure security groups are set up properly to allow SSH and PostgreSQL connections to your VPS so you can tinker with it. TCP Connection to port 22 should be allowed for SSH and TCP Connection to port 5432 should be allowed for PostgreSQL.

    This software runs (alarming on high CPU usage, but runs) on AWS's free tier t2.micro instance. You can set up a VPS on AWS and install Ubuntu 22.04 on it. You can also use other VPS providers like DigitalOcean, Linode, etc. Just make sure you have enough resources to run the software.

    Tried this on Oracle's free tier but it freezes with high CPU usage, so I don't recommend it.

1. **Dependencies**
    This project requires the following Python libraries:

    - **pandas**: A powerful data structures and data analysis library.
    - **pytz**: A library for handling timezone calculations.
    - **requests**: A library for making HTTP requests.
    - **python-dotenv**: A library for loading environment variables from .env files.
    - **protobuf**: Google's data interchange format, needed to handle GTFS realtime data.
    - **sqlalchemy**: A SQL toolkit and Object-Relational Mapping (ORM) system for Python, providing a full suite of well known enterprise-level persistence patterns.
    - **psycopg2**: A PostgreSQL database adapter for Python.
    - **paramiko**: A Python (2.7, 3.4+) implementation of the SSHv2 protocol, providing both client and server functionality.

    You can install all these packages using pip:

    ```shell
    # Install pip
    sudo apt-get install python3-pip

    # Install libpq-dev for psycopg2
    sudo apt-get install libpq-dev

    # Install the required packages
    pip install pandas pytz requests python-dotenv protobuf sqlalchemy psycopg2 paramiko
    ```

    Ensure that the Python packages are installed in the same environment where you intend to run your Python scripts.

    Additionally, the `lib` module (a local module in this project) is used. This module is a folder containing generated protocol buffer code to handle GTFS data. Please ensure this is properly set up in your environment. It is located in the `lib` folder, inside the root folder of this repository.

2. **Environment Setup:**
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
    # Path to put the csv file in the local machine : '/Users/xxxxxx/data.csv'
    LOCAL_CSV_FILE_PATH=<Path to your local csv file. it is erased after updating the table>
    # Path to your private key file
    PRIVATE_KEY_PATH=<Path to your private key file>
    ```

    Be sure to replace all `<Your ...>` placeholders with your actual data.


3. **Database Setup:**
    You need to create three tables in your PostgreSQL database: `gtfs_data` for the historical data, `trip_updates` for the realtime data and `trip_updates_with_diffs` for the data with the difference between the scheduled and actual arrival times.

    The required SQL commands for creating these tables are as follows:

    ```sql
    CREATE TABLE IF NOT EXISTS public.gtfs_data
    (
        trip_id text COLLATE pg_catalog."default" NOT NULL,
        start_date date NOT NULL,
        stop_sequence bigint NOT NULL,
        stop_id bigint NOT NULL,
        route_id text COLLATE pg_catalog."default" NOT NULL,
        stop_name text COLLATE pg_catalog."default" NOT NULL,
        route_long_name text COLLATE pg_catalog."default" NOT NULL,
        arrival_time timestamp with time zone,
        departure_time timestamp with time zone,
        geo_coordinates text COLLATE pg_catalog."default" NOT NULL,
        CONSTRAINT gtfs_data_pkey PRIMARY KEY (trip_id, start_date, stop_sequence, stop_id)
    )
    ```

    ```sql
    CREATE TABLE IF NOT EXISTS public.trip_updates
    (
        trip_id text COLLATE pg_catalog."default" NOT NULL,
        start_date date NOT NULL,
        stop_sequence integer NOT NULL,
        stop_id text COLLATE pg_catalog."default" NOT NULL,
        arrival_time timestamp with time zone NOT NULL DEFAULT '1969-12-31 21:00:00-03'::timestamp with time zone,
        departure_time timestamp with time zone NOT NULL DEFAULT '1969-12-31 21:00:00-03'::timestamp with time zone,
        weather_group text COLLATE pg_catalog."default",
        weather_description text COLLATE pg_catalog."default",
        created_at timestamp with time zone,
        updated_at timestamp with time zone,
        CONSTRAINT trip_updates_pkey PRIMARY KEY (trip_id, start_date, stop_sequence, stop_id)
    )
    ```

    ```sql
    CREATE TABLE IF NOT EXISTS public.trip_updates_with_diffs
    (
        trip_id text COLLATE pg_catalog."default" NOT NULL,
        start_date date NOT NULL,
        stop_sequence integer NOT NULL,
        stop_id bigint NOT NULL,
        route_id text COLLATE pg_catalog."default",
        stop_name text COLLATE pg_catalog."default",
        route_long_name text COLLATE pg_catalog."default",
        actual_arrival_time timestamp with time zone,
        scheduled_arrival_time timestamp with time zone,
        arrival_time_diff_in_minutes double precision,
        actual_departure_time timestamp with time zone,
        scheduled_departure_time timestamp with time zone,
        departure_time_diff_in_minutes double precision,
        average_diff_in_minutes double precision,
        weather_group text COLLATE pg_catalog."default",
        weather_description text COLLATE pg_catalog."default",
        day_type text COLLATE pg_catalog."default",
        sudbury_hour_of_day integer,
        geo_coordinates text COLLATE pg_catalog."default" NOT NULL,
        created_at timestamp with time zone,
        updated_at timestamp with time zone,
        CONSTRAINT trip_updates_with_diffs_pkey PRIMARY KEY (trip_id, start_date, stop_sequence, stop_id)
    )
    ```

4. **Execution:**
    The `realtime_extractor.py` script is executed on a regular basis on a remote server. This script pulls data from the GTFS real-time feed and stores it in the `trip_updates` table. The `historical_extractor.py` script, on the other hand, should be run manually as needed to pull and store historical data in the `gtfs_data` table.

    You can set the `realtime_extractor.py` script to run as a cron job on your remote server. To make the script run every minute, edit the crontab file with `crontab -e` and add the following line:

    ```bash
    * * * * * /usr/bin/python3 /path/to/realtime_extractor.py
    ```
    
    Be sure to replace `/path/to/realtime_extractor.py` with the actual path to the Python script on your server.

5. **Data Transfer:**
    Since the analysis that will be made here are costly in terms of computer power, I decided to do it locally instead of on the remote computer, which is somewhat limited. To do this a Python script, `get_realtime.py` is employed. This script uses the Paramiko library for SSH connections and commands, psycopg2 for PostgreSQL database interaction, and dotenv for environment variable management. The script is executed on a local machine and connects to a remote server to download the most recent data from the `trip_updates` table. The data is then stored in a local CSV file, which is then used to update the `trip_updates` table in the local database.

## Data analysis

The `diff_times.py` script is used to analyze the timeliness of buses. It populates the table with the new data using a SQL query. This query joins the `trip_updates` table (containing real-time data) and the `gtfs_data` table (containing historical data), calculates the differences in arrival and departure times, and stores this data in the `trip_updates_with_diffs` table.

Since past data with exact times that buses got to their stops is not freely available, I decided to query the realtime data every minute to get the updated ETA of the buses to get the most up to date time to arrival. This data is then compared to the scheduled time to arrival to get the difference in time.

### Dashboard access

To access the dashboard you can follow this link: [Sudbury's Transit Efficiency Analysis](https://lookerstudio.google.com/reporting/27a19cc1-0a40-453a-ae12-5bb09e7de7e9)

![Dashboard](public/Dashboard%20-%20STEA.png?raw=true "Sudbury Transit Efficiency Analysis")

1. **Bus Timeliness**

    This analysis has shown which times of the day are the most and least efficient in terms of bus timeliness. It was possible to filter by routes, stops, time of day, and day of the week. The results are shown in the form of a bar chart.

2. **Route Efficiency**

    Using a map it is possible to see which areas have more routes and which have less. This can be seen with a heatmap with the stops plotted on top. The routes are also plotted on the map and can be filtered by day of the week and time of day.

3. **Peak Hour Analysis**

    Through both bar chart and heatmap, it is possible to see which times of the day are the most and least efficient in terms of bus timeliness.

## Future Work

- [x] Add weather data to the database to see how it affects bus timeliness.
- [ ] Add holidays to the database to see how it affects bus timeliness.
- [ ] Create a machine learning model to predict bus timeliness.

## License
This project is licensed under the terms of the [MIT License](LICENSE.md).

## Contact Information
If you have any queries or suggestions, feel free to reach out:

E-mail: andre.szlima1@gmail.com
LinkedIn: https://www.linkedin.com/in/andreszlima/