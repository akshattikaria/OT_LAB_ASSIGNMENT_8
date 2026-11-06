-- customer
SELECT id,slot,total_cents,status FROM bookings WHERE customer_id=?
 ORDER BY slot DESC,id DESC LIMIT 20;

-- station
SELECT COUNT(*),SUM(total_cents),SUM(energy_wh) FROM bookings
 WHERE station_id=? AND slot>=? AND slot<?;

-- confirmed
SELECT COUNT(*),SUM(total_cents) FROM bookings
 WHERE station_id=? AND status='confirmed' AND slot>=? AND slot<?;

-- status
SELECT id,slot,station_id,total_cents FROM bookings
 WHERE status=? AND slot>=? AND slot<? ORDER BY slot,id LIMIT 80;

-- daily
SELECT slot/24 AS day,COUNT(*),SUM(total_cents) FROM bookings
 WHERE slot>=? AND slot<? GROUP BY day ORDER BY day;

-- city
SELECT s.city,COUNT(*),SUM(b.total_cents) FROM stations AS s
 JOIN bookings AS b ON b.station_id=s.id
 WHERE s.city=? AND b.slot>=? AND b.slot<? AND b.status='confirmed'
 GROUP BY s.city ORDER BY s.city;
