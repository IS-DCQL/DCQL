SELECT event_number,
       SQRT(POWER(SUM(px), 2) + POWER(SUM(py), 2)) AS met
FROM particle
WHERE status = 1
GROUP BY event_number
HAVING SQRT(POWER(SUM(px), 2) + POWER(SUM(py), 2)) > 50000;
