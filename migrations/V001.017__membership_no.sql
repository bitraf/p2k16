ALTER TABLE account
  DROP COLUMN IF EXISTS system;

ALTER TABLE account
  ADD COLUMN system BOOLEAN NOT NULL DEFAULT FALSE;

INSERT INTO public.account (created_at, updated_at, username, email, system)
VALUES (current_timestamp, current_timestamp, 'system', 'root@bitraf.no', TRUE);
