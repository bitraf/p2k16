ALTER TABLE circle
  ALTER description DROP NOT NULL,
  DROP CONSTRAINT IF EXISTS circle_description_key;
