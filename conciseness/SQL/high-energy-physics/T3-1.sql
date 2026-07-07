SELECT event_number, particle_id
FROM particle
WHERE pid IN (11, -11) AND status = 1;
