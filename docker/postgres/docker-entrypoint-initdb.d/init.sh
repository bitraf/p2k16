#!/bin/bash

echo "Copying postgresql.conf to /var/lib/postgresql/data/postgresql.conf"
cp /docker-entrypoint-initdb.d/postgresql.conf /var/lib/postgresql/data/postgresql.conf

echo "Creating cms user"
gosu postgres postgres --single -jE <<-EOSQL
create user cms with password '$P2K16_DB_PASSWORD';
EOSQL

echo "Creating dabase"
gosu postgres postgres --single -jE <<-EOSQL
CREATE DATABASE "p2k16" WITH OWNER "p2k16";
EOSQL
