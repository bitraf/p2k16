UPDATE account_badge
SET awarded_by = created_by
WHERE awarded_by IS NULL;

ALTER TABLE account_badge
  ALTER COLUMN awarded_by DROP NOT NULL;
