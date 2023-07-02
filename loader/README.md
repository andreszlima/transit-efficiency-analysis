# Real-time Data Transfer Script

This Python script, named `get_realtime.py`, is designed to facilitate the transfer of real-time data from a remote server to a local PostgreSQL database. The script uses several libraries, such as Paramiko for SSH connections and commands, psycopg2 for PostgreSQL database interactions, and dotenv for environment variable management.

The following steps are executed by the script:

## 1. Create an SSH Client
Using the Paramiko library, the script establishes an SSH connection to the remote server using the SSH username and private key file defined in the environment variables.

## 2. Export Data from Remote PostgreSQL to CSV
The script then exports data from the remote PostgreSQL table to a CSV file on the remote server. This is done using the `\COPY` SQL command, which is executed through the `psql` command-line interface.

## 3. Transfer CSV file
The script uses the SCP (Secure Copy Protocol) to transfer the generated CSV file from the remote server to the local machine.

## 4. Import CSV file to Local PostgreSQL
The data from the CSV file is then imported into a local PostgreSQL table. This is done using psycopg2's `execute_values` method, which can efficiently execute bulk inserts.

## 5. Truncate the Remote Real-time Table
After successfully importing the data to the local table, the script truncates the remote real-time table to save storage space.

## 6. Remove Local and Remote CSV Files
Finally, the script cleans up by deleting both the local and remote CSV files created during the data transfer process.

## Usage
To use this script, it must be executed periodically, depending on how frequently the data updates and the needs of your analysis. It can be scheduled as a cron job or incorporated into a data pipeline.

## Environment Variables
This script relies on environment variables stored in a .env file. The following environment variables must be defined:

- `REMOTE_DB_USERNAME`: The username for the remote PostgreSQL database.
- `REMOTE_DB_PASSWORD`: The password for the remote PostgreSQL database.
- `REMOTE_DB_NAME`: The name of the remote PostgreSQL database.
- `REALTIME_TABLE`: The name of the table in the remote PostgreSQL database.
- `VPS_USERNAME`: The username for the VPS (Virtual Private Server).
- `VPS_SERVER_IP`: The IP address of the VPS.
- `LOCAL_DB_NAME`: The name of the local PostgreSQL database.
- `PRIVATE_KEY_PATH`: The path to the private SSH key.
- `LOCAL_DB_USERNAME`: The username for the local PostgreSQL database.
- `LOCAL_DB_PASSWORD`: The password for the local PostgreSQL database.

## Dependencies
To run this script, you need to have Python installed along with the following Python packages:
- `paramiko`
- `psycopg2`
- `python-dotenv`

These can be installed using pip:

```bash
pip install paramiko psycopg2 python-dotenv
```