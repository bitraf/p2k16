DO $$
DECLARE
  seq_row information_schema.sequences%ROWTYPE;
  col_row information_schema.columns%ROWTYPE;

  sql     TEXT;
BEGIN
  -- Drop default values for all id columns
  FOR col_row IN (SELECT *
                  FROM information_schema.columns
                  WHERE table_schema = 'public' AND
                        column_name = 'id') LOOP

    SELECT format('ALTER TABLE %I ALTER COLUMN id DROP DEFAULT', col_row.table_name)
    INTO sql;
    RAISE NOTICE 'exec: %', sql;
    EXECUTE sql;
  END LOOP;

  -- Drop all id sequences
  FOR seq_row IN (SELECT *
                  FROM information_schema.sequences c
                  WHERE c.sequence_schema = 'public'
                  ORDER BY c.sequence_name) LOOP

    SELECT format('DROP SEQUENCE %I', seq_row.sequence_name)
    INTO sql;
    RAISE NOTICE 'exec: %', sql;
    EXECUTE sql;
  END LOOP;

  DROP SEQUENCE IF EXISTS id_seq;
  CREATE SEQUENCE id_seq
    START 100000;

  DROP SEQUENCE IF EXISTS transaction_id_seq;
  CREATE SEQUENCE transaction_id_seq
    START 100000;

  -- Set default to id_seq for all non-version tables
  FOR col_row IN (SELECT *
                  FROM information_schema.columns
                  WHERE table_schema = 'public' AND
                        table_name NOT LIKE '%_version' AND
                        column_name = 'id') LOOP

    SELECT format('ALTER TABLE %I ALTER COLUMN id SET DEFAULT nextval(''id_seq'')', col_row.table_name)
    INTO sql;
    RAISE NOTICE 'exec: %', sql;
    EXECUTE sql;
  END LOOP;

  GRANT ALL ON id_seq TO "p2k16-web";
  GRANT ALL ON transaction_id_seq TO "p2k16-web";
END;
$$;
