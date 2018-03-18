ALTER TABLE account
  DROP COLUMN IF EXISTS membership_number;

ALTER TABLE account
  ADD COLUMN membership_number INT;
