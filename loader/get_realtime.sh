    #!/bin/bash

    # Source environment variables
    source "../scripts/.env"

    # Remote variables
    DB_USERNAME=$REMOTE_DB_USERNAME
    DB_PASSWORD=$REMOTE_DB_PASSWORD
    DB_NAME=$REMOTE_DB_NAME
    TABLE_NAME=$REALTIME_TABLE
    REMOTE_DUMP_FILE_PATH=$VPS_REMOTE_DUMP_FILE_PATH

    # Local variables
    USERNAME=$VPS_USERNAME
    SERVER_IP=$VPS_SERVER_IP
    LOCAL_DUMP_FILE_PATH=$LOCAL_DUMP_FILE_PATH
    LOCAL_DB_NAME=$LOCAL_DB_NAME
    PRIVATE_KEY_PATH=$PRIVATE_KEY_PATH
    LOCAL_USERNAME=$LOCAL_DB_USERNAME
    LOCAL_PASSWORD=$LOCAL_DB_PASSWORD

    # Create a dump file on the remote server
    ssh -i $PRIVATE_KEY_PATH $USERNAME@$SERVER_IP "PGPASSWORD=$DB_PASSWORD pg_dump -Fc -U $DB_USERNAME -d $DB_NAME -t $TABLE_NAME -f $REMOTE_DUMP_FILE_PATH" && \
    echo "Dump file $REMOTE_DUMP_FILE_PATH created for table $TABLE_NAME." || \
    echo "Failed to create dump file."

    # Transfer the dump file
    scp -i $PRIVATE_KEY_PATH $USERNAME@$SERVER_IP:$REMOTE_DUMP_FILE_PATH $LOCAL_DUMP_FILE_PATH && \
    echo "Dump file transferred to local machine." || \
    echo "Failed to transfer dump file."

    # Connect to local database and drop the existing table
    PGPASSWORD=$LOCAL_PASSWORD psql -U $LOCAL_USERNAME -d $LOCAL_DB_NAME -h localhost << EOF

    DROP TABLE IF EXISTS $TABLE_NAME;

    EOF

    echo "Existing table dropped."

    # Restore the table from the dump file
    PGPASSWORD=$LOCAL_PASSWORD pg_restore -U $LOCAL_USERNAME -d $LOCAL_DB_NAME -v -F c -t $TABLE_NAME $LOCAL_DUMP_FILE_PATH && \
    echo "Table $TABLE_NAME restored from $LOCAL_DUMP_FILE_PATH." || \
    echo "Failed to restore table."

    # Remove local dump file
    rm $LOCAL_DUMP_FILE_PATH && \
    echo "Local dump file removed." || \
    echo "Failed to remove local dump file."

    # Remove remote dump file
    ssh -i $PRIVATE_KEY_PATH $USERNAME@$SERVER_IP "rm $REMOTE_DUMP_FILE_PATH" && \
    echo "Remote dump file removed." || \
    echo "Failed to remove remote dump file."