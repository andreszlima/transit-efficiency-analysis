import os
import paramiko
from dotenv import load_dotenv
import psycopg2
import subprocess
import csv
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv("../scripts/.env")

# Remote variables
DB_USERNAME = os.getenv("REMOTE_DB_USERNAME")
DB_PASSWORD = os.getenv("REMOTE_DB_PASSWORD")
DB_NAME = os.getenv("REMOTE_DB_NAME")
TABLE_NAME = os.getenv("REALTIME_TABLE")
REMOTE_CSV_FILE_PATH = "/tmp/data.csv"  # Temporary location to store CSV on remote server

# Local variables
USERNAME = os.getenv("VPS_USERNAME")
SERVER_IP = os.getenv("VPS_SERVER_IP")
LOCAL_CSV_FILE_PATH = os.getenv("LOCAL_CSV_FILE_PATH")  # Location to store downloaded CSV on local machine
LOCAL_DB_NAME = os.getenv("LOCAL_DB_NAME")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
LOCAL_USERNAME = os.getenv("LOCAL_DB_USERNAME")
LOCAL_PASSWORD = os.getenv("LOCAL_DB_PASSWORD")

def main():
    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=USERNAME, key_filename=PRIVATE_KEY_PATH)

    # Export data from remote PostgreSQL table to a CSV file
    print('Creating CSV file on the remote server...')
    stdin, stdout, stderr = ssh.exec_command(f"PGPASSWORD={DB_PASSWORD} psql -U {DB_USERNAME} -d {DB_NAME} -c '\\COPY (SELECT * FROM {TABLE_NAME}) TO {REMOTE_CSV_FILE_PATH} CSV'")
    stdout.channel.recv_exit_status()  # Wait until the command finishes
    print('CSV file created.')

    # Download CSV file from remote server to local machine
    print('Transferring CSV file...')
    sftp = ssh.open_sftp()
    sftp.get(REMOTE_CSV_FILE_PATH, LOCAL_CSV_FILE_PATH)
    sftp.close()
    print('CSV file transferred.')

    # Import CSV file to local PostgreSQL table
    print('Importing CSV file to local PostgreSQL table...')
    with psycopg2.connect(f"dbname={LOCAL_DB_NAME} user={LOCAL_USERNAME} password={LOCAL_PASSWORD}") as conn:
        with conn.cursor() as cur:
            with open(LOCAL_CSV_FILE_PATH, 'r') as f:
                execute_values(cur, f"INSERT INTO {TABLE_NAME} VALUES %s ON CONFLICT DO NOTHING", csv.reader(f))
            conn.commit()
    print('CSV file imported.')

    # Truncate the remote realtime table
    print('Truncating the remote realtime table...')
    stdin, stdout, stderr = ssh.exec_command(f"PGPASSWORD={DB_PASSWORD} psql -U {DB_USERNAME} -d {DB_NAME} -c 'TRUNCATE TABLE {TABLE_NAME};'")
    stdout.channel.recv_exit_status()  # Wait until the command finishes
    print('Remote realtime table truncated.')

    # Remove local CSV file
    print('Removing local CSV file...')
    os.remove(LOCAL_CSV_FILE_PATH)
    print('Local CSV file removed.')

    # Remove remote CSV file
    print('Removing remote CSV file...')
    stdin, stdout, stderr = ssh.exec_command(f"rm {REMOTE_CSV_FILE_PATH}")
    stdout.channel.recv_exit_status()  # Wait until the command finishes
    print('Remote CSV file removed.')

    # Close SSH connection
    ssh.close()

if __name__ == '__main__':
    main()
