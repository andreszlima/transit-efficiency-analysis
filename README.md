# Sudbury Transit Efficiency Analysis

![People leaving bus](public/canada%20bus.png?raw=true "Sudbury Transit Efficiency Analysis")

## Project Description
This project aims to analyze the efficiency and effectiveness of Sudbury's bus service. Leveraging publicly available data, the analysis is structured around three main objectives: 

1. **Bus Timeliness:** Analysis of scheduled versus actual bus arrival times.
2. **Route Efficiency:** Evaluation of the distribution of bus stops and service frequency across different routes.
3. **Peak Hour Analysis:** Identification of the busiest hours for the Sudbury bus transit system.

## Data Source
The data used in this project is sourced from the [Sudbury's open data Portal](http://sudbury.tmix.se/). This dataset provides detailed route and schedule information for all surface route operations. Data is downloaded, cleaned, and stored using a Python script (`extractor.py`), which is run on a regular basis to collect the most recent data.

## Tools and Technologies
* Python for data gathering, data cleaning, and analysis. Key libraries used include Pandas for data manipulation, requests for data downloading, and SQLAlchemy for database connection.
* PostgreSQL for data storage and management. Database queries are written in SQL for extracting insights from the data.
* Future work may include using Apache Airflow to automate and schedule data pipelines, and creating dashboards for data visualization.

## Setup & Execution
The Python script `extractor.py` is used to download data, parse the data into a structured format, and insert the data into a PostgreSQL database. Before running the script, make sure to install all necessary Python libraries and set up the PostgreSQL database. Set your database connection string as an environment variable in a .env file. Then you can execute the script with `python extractor.py`.

## Findings
_To be added_

## Visualizations
_To be added_
