#!/bin/bash

echo "Copying postgresql.conf to /var/lib/postgresql/data/postgresql.conf"
cp /docker-entrypoint-initdb.d/postgresql.conf /var/lib/postgresql/data/postgresql.conf
chmod 0700 -R /var/lib/postgresql/data/
chown postgres /var/lib/postgresql/data/

echo "Creating p2k16 user"
gosu postgres postgres --single -jE <<-EOSQL
create user p2k16 with password '$P2K16_DB_PASSWORD';
EOSQL

echo "Creating dabase"
gosu postgres postgres --single -jE <<-EOSQL
CREATE DATABASE "p2k16" WITH OWNER "p2k16";
EOSQL
