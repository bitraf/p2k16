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
  * <s>Send by email</s>
  * <s>Set new password</s>
  * Create some @annotations to do simple circle membership checks. To be used after @registry.

# TODOs before dropping p2k12

* Migrate data from p2k12 database
* <s>Actually open doors.</s>

# TODOs post production / p2k12 migration

* Fix bitraf.no graph

# TODOs (fix at any time)

* Add word completion to Add Badge text field.
* Empty text field after clicking Add badge on user profile.
* Show success message after adding badge on user profile.
* Fix duplicate-check for badge names.
* Add word cloud or similar for badges on Bitraf front page, to increase front page utility and engagement.
* Add delete badge-button for self-made badges.
* Limit line length for badges on user profile.
* Drop BIGSERIAL on _version tables. Should be BIGINT instead.
* Prevent updates to certain fields like Account.username.
  SQLAlchemy's event systems seems like a useful method: http://docs.sqlalchemy.org/en/latest/orm/events.html

# Badge system

## Motivation

 * Enforce users have necessary course for dangerous machines
 * Make holding courses more attractive
 * Easier to find who knows what. Show a list/word cloud of the competence of the people who has recently checked in at
   Bitraf. On the front page, perhaps show a list of *all* active people's competence.
 * Encourage people to be active members at Bitraf

## Examples

Badges is a way to tell something about a user. They have no monetary value, but can have a lot of social value.

Certain badges are restricted so that they can only be given to a person by someone else (aka karma badges), and other
badges are restricted so that only certain users can award them (for example course instructors).

Most badges can be awarded multiple times too.

Badge categories:

 * Competence levels (badges required to operate certain tools that require course)

   - laser cutter
   - CNC-operator
   - lathe

 * Interest areas: (for expressing hobbies and competence levels)

   - laser cutting
   - woodworking
   - metalworking
   - soldering
   - KiCAD, Eagle
   - SMT
   - PCB-etching
   - oscilloscope

 * Karma badges

   - Cleaner
   - Dugnader
   - Bitraf project fixer
   
 * Various badge ideas
    - Badge "Initiator"\"dugnadsånd"? Bade for fixing something at Bitraf, i.e repairing laser, workshop mentoring, implementing web solutions (like this badge thingie), etc.
    - Profession badge category, i.e Professional Programmer, Professional Electrician, Professional Carpenter.
