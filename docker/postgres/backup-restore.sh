#!/bin/bash

# Checking number of databases
if [ ! $(ls -1 /backup/*.psql | wc -l) -eq 1 ]
	then
	echo "Found Zero, or more than one .psql files in /backup, Need to have just one please."
	exit 1
fi

PG_FILE=$(ls /backup/*.psql | tail -n 1)

echo "Restoring database"
export PGPASSWORD=$POSTGRES_ENV_P2K16_DB_PASSWORD
pg_restore -h localhost -U cms -d cms -O $PG_FILE
