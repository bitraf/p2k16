#!/bin/bash

echo "Dumping cms db"
export PGPASSWORD=$POSTGRES_ENV_P2K16_DB_PASSWORD
pg_dump -h localhost -U p2k16 -Fc -v -f /backup/cms.psql
echo "Db dump finished"
