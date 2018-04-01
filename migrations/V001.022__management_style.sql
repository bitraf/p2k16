ALTER TABLE circle
  DROP COLUMN IF EXISTS management_style,
  DROP COLUMN IF EXISTS admin_circle;

ALTER TABLE circle_version
  DROP COLUMN IF EXISTS management_style,
  DROP COLUMN IF EXISTS admin_circle;

ALTER TABLE circle
  ADD COLUMN management_style VARCHAR DEFAULT 'ADMIN_CIRCLE',
  ADD COLUMN admin_circle BIGINT REFERENCES circle;

ALTER TABLE circle
  ALTER COLUMN management_style DROP DEFAULT;

ALTER TABLE circle_version
  ADD COLUMN management_style VARCHAR,
  ADD COLUMN admin_circle BIGINT;

UPDATE circle
SET management_style = 'SELF_ADMIN'
WHERE name = 'admin';
