# Getting started

Creating the database:

    # sudo -i postgres psql

    CREATE USER "p2k16" ENCRYPTED PASSWORD 'p2k16';
    CREATE USER "p2k16-web" ENCRYPTED PASSWORD 'p2k16-web';
    CREATE DATABASE "p2k16" OWNER "p2k16";

Running the application:

    # ./run-p2k16-web

This will fail unless you have the required applications installed.

# Thoughs


* Office users, support companies that give access to more than one user
* Certifications, allow users to have certifications.
* control and register access to items (for example doors, machines and equipment).
  * Items have different requirements, the main door has active membership or being an office user
  * A machine may require active membership *and* valid certification for the particular machine

# Door access

The door application is migrated to the p2k16 site. Existing users won't be able to log in, but can be redirected to
the p2k12 site to migrate their user

## p2k12 migration

p2k12.bitraf.no authenticates people, on authentication it creates the user in p2k16 allowing them to set a new password.

p2k16 can read active memberships from p2k12 until the stripe code is moved.

