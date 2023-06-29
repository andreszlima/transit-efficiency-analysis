## Data Transfer Script

This is a Python script, `get_realtime.py`, to facilitate the transfer of real-time data from a remote server to a local PostgreSQL database. This script uses the Paramiko library for SSH connections and commands, psycopg2 for PostgreSQL database interaction, and dotenv for environment variable management.

Below is a brief description of the steps executed by the script:

1. **Create an SSH Client:** Using Paramiko, the script establishes an SSH connection to the remote server using the SSH username and private key file defined in the environment variables.

2. **Export Data from Remote PostgreSQL to CSV:** The script then exports data from the remote PostgreSQL table to a CSV file on the remote server. This is done via the `\COPY` SQL command executed via the `psql` command-line interface.

3. **Transfer CSV file:** The script uses the SFTP protocol to transfer the generated CSV file from the remote server to the local machine.

4. **Import CSV file to Local PostgreSQL:** The data from the CSV file is then imported into a local PostgreSQL table. This is done using psycopg2's `execute_values` method, which can efficiently execute bulk inserts.

5. **Truncate the Remote Real-time Table:** After successfully importing the data to the local table, the script truncates the remote real-time table to save storage space.

6. **Remove Local and Remote CSV Files:** Finally, the script cleans up by deleting both the local and remote CSV files created during the data transfer process.

This script should be run periodically, depending on how frequently the data updates and your analysis needs. It can be scheduled as a cron job or incorporated into a data pipeline.