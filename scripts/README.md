# GTFS Data Processing Scripts

This project is composed of three Python scripts designed to fetch and process GTFS data. This data includes both historical and real-time transit feeds.

## Script Details

### Extraction of Historical Data

`historical_extractor.py` is responsible for downloading a ZIP file containing historical GTFS data from a specified URL. The script extracts the ZIP file and reads the data (CSV format) into pandas dataframes. 

The data is then processed and cleaned in chunks to handle memory efficiently, especially for large datasets. After processing, the data is inserted into a local PostgreSQL database.

### Extraction of Real-time Data

`realtime_extractor.py` is tasked with downloading real-time GTFS data in the form of Protocol Buffer (protobuf) files from a specified URL. It then decodes the protobuf file and converts the data into a pandas dataframe.

The dataframe undergoes further processing and cleaning before being inserted into a remote PostgreSQL database.

### Diffing of Historical and Real-time Data to get the delays

`diff_times.py` is the final script in this workflow. It connects to the local PostgreSQL database, and deletes outdated data, ensuring that the database stays up-to-date and manageable. 

The script then populates the database with new data by executing an SQL query. The new data includes the consolidated historical and real-time GTFS data processed by the previous two scripts.

## Dependencies

To run these scripts, you need to have Python 3.6+ installed along with the following Python packages:

- pandas
- requests
- psycopg2
- protobuf

You can install these packages using pip:

```shell
pip install pandas requests psycopg2 protobuf
```

You also need to have PostgreSQL installed and a database set up to store the processed GTFS data.

## Usage

To use these scripts, you need to set the URLs for the historical and real-time GTFS data feeds as well as the local and remote PostgreSQL database credentials in a `.env` file in the `scripts` directory, as stated in the [README](../README.md) for this project.

You can then run each script from the command line as follows:

```shell
python historical_extractor.py
python realtime_extractor.py
python diff_times.py
```

Each script will output logs to the console to help you monitor its progress and troubleshoot any issues that might arise.

It is recommended that `realtime_extractor.py` runs inside a VPS (Virtual Private Server) to ensure that the real-time data is always available. You can use a cron job to schedule the script to run periodically. Then, you can run `../loader/get_realtime.py` to fetch the real-time data from the remote database for local processing, since this can be demanding on system resources.