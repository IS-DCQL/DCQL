DELETE FROM particle WHERE status <> 1;
DELETE FROM particle_link
WHERE particle_id NOT IN (SELECT particle_id FROM particle)
   OR child_id    NOT IN (SELECT particle_id FROM particle);
