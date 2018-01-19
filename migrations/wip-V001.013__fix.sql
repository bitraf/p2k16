-- all tables, views, functions, types, ...
-- ALTER ... OWNER TO p2k16;

-- SET SESSION AUTHORIZATION p2k16;

-- Indexes:
--     "accounts_pkey" PRIMARY KEY, btree (id)
--     "accounts_lower_name" UNIQUE, btree (lower(name))
--     "accounts_name" UNIQUE, btree (name)

-- Check constraints:
--     "members_email_check" CHECK (email ~~ '%@%.%'::text)
--     "members_full_name_check" CHECK (length(full_name) > 0)
--     "nonnegative_price" CHECK (price >= 0::numeric)

-- alle tabeller: timestamptz i stedet for timestamp without time zone
