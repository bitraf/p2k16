DO $$
DECLARE
    ref CURSOR FOR
    SELECT *
    FROM information_schema.columns c
    WHERE c.table_schema = 'public'
          AND c.data_type = 'timestamp without time zone'
          AND c.table_name NOT IN ('schema_version')
    order by c.table_schema, c.table_name, c.column_name;
  sql TEXT;
BEGIN
  FOR row IN ref LOOP
    SELECT format('ALTER TABLE %I.%I ALTER COLUMN %I TYPE TIMESTAMP WITH TIME ZONE ',
                  row.table_schema,
                  row.table_name,
                  row.column_name)
    INTO sql;
    RAISE NOTICE 'exec: %', sql;
    EXECUTE sql;
  END LOOP;
END;
$$;
