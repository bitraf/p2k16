# Getting started without Docker

Install:

- virtualenv
- bower

Creating the database:

    # sudo -u postgres psql -f database-setup.sql

Running the application:

    # ./run-p2k16-web

This will fail unless you have the required applications installed.

# Creating SQL migrations

We use Flyway (https://flywaydb.org) to manage the schema. Flyway is a upgrade-only, sql-only tool (at least in our
setup) to manage SQL databases. We're smart and are using PostgreSQL which support transactional changes to the schema.

After checking out the code and creating the database, run `./flyway migrate` to migrate the database.

If you want to change the schema, create a new file under `migrations/` called `V001.NNN__clever_comment.sql`. If more
than one person is creating a schema at the same time you will get a conflict when the code is merged.

# Thoughts

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

# TODOs before deploying in prod

* Implement recover password feature so people can create passwords in p2k16. Parts:
  * <s>Request new password</s>
  * Send by email
  * <s>Set new password</s>
  * Create some @annotations to do simple circle membership checks. To be used after @registry.

# TODOs before dropping p2k12

* Migrate data from p2k12 database
* Actually open doors.
  * Audit log

# TODOs post production / p2k12 migration

* Fix bitraf.no graph

# TODOs (fix at any time)

* Drop BIGSERIAL on _version tables. Should be BIGINT instead.


# Badge system

## Motivation

 * Enforce users have neccesary course for dangerous machines
 * Make holding courses more atractive
 * Easier to find who knows what
 * Encourage people to be active members at Bitraf

## Examples

 * lasercutter
 * CNC-operator
 * woodworking
 * metalworking
 * lathe

 * soldering
 * Kicad, Eagle
 * SMT
 * PCB-etching
 * oscilloscope

## Data model

BadgeDescription

 * id/slug
 * title
 * icon
 * needs_certification

AccountBadge

 * account FOREIGN NON NULL
 * badge_description NULL
 * awarded_at NOT NULL
 * awarded_by NULL

