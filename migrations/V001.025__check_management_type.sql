UPDATE circle
SET admin_circle = (SELECT id
                    FROM circle
                    WHERE name = 'admin')
WHERE
  management_style = 'ADMIN_CIRCLE' AND
  admin_circle IS NULL;

ALTER TABLE circle
  DROP CONSTRAINT IF EXISTS circle_management_style;

ALTER TABLE circle
  ADD CONSTRAINT circle_management_style CHECK (
  (management_style = 'ADMIN_CIRCLE' AND admin_circle IS NOT NULL) OR
  (management_style = 'SELF_ADMIN'));
