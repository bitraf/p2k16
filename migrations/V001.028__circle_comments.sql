ALTER TABLE circle
  DROP COLUMN IF EXISTS comment_required_for_membership;

ALTER TABLE circle_version
  DROP COLUMN IF EXISTS comment_required_for_membership;

ALTER TABLE circle
  ADD COLUMN comment_required_for_membership BOOLEAN DEFAULT FALSE;

ALTER TABLE circle
  ALTER COLUMN comment_required_for_membership DROP DEFAULT;

ALTER TABLE circle_version
  ADD COLUMN comment_required_for_membership BOOLEAN;
