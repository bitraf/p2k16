-- TODO: remove lined with p2k16-admin, the user is not used any more.
REVOKE ALL PRIVILEGES ON DATABASE p2k16 FROM "p2k16-admin";
REVOKE ALL PRIVILEGES ON SCHEMA public FROM "p2k16-admin";
REVOKE ALL PRIVILEGES ON DATABASE p2k16 FROM "p2k16-flyway";
REVOKE ALL PRIVILEGES ON SCHEMA public FROM "p2k16-flyway";
REVOKE ALL PRIVILEGES ON SCHEMA public FROM "p2k16-ldap";
REVOKE ALL PRIVILEGES ON SCHEMA public FROM "p2k16-web";

DROP DATABASE IF EXISTS "p2k16";

DROP USER IF EXISTS "p2k16-admin";
DROP USER IF EXISTS "p2k16-flyway";
DROP USER IF EXISTS "p2k16-ldap";
DROP USER IF EXISTS "p2k16-web";
DROP USER IF EXISTS "p2k16";

-- This section matches what Bitraf infrastructure's Ansible script does.

-- This is the default owner of all objects
CREATE USER "p2k16"
  NOLOGIN;

-- Regular users that can log in
CREATE USER "p2k16-flyway"
  ENCRYPTED PASSWORD 'p2k16-flyway';

CREATE USER "p2k16-web"
  ENCRYPTED PASSWORD 'p2k16-web';

CREATE USER "p2k16-ldap"
  ENCRYPTED PASSWORD 'p2k16-ldap';

CREATE DATABASE p2k16 OWNER p2k16;

GRANT USAGE ON SCHEMA PUBLIC TO "p2k16-flyway";
GRANT USAGE ON SCHEMA PUBLIC TO "p2k16-web";
GRANT CREATE ON DATABASE p2k16 TO "p2k16-flyway";
