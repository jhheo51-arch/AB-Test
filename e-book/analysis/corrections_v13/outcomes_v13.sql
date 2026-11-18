DROP VIEW IF EXISTS outcomes;
CREATE VIEW outcomes AS SELECT a.assignment_id,a.customer_id,a.arm,a.assigned_day,
 MAX(CASE WHEN e.event_type='booking' AND e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS booked_28,
 MAX(CASE WHEN e.event_type='test_drive_completed' AND e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS completed_28,
 MAX(CASE WHEN e.event_type='consent_withdrawn' AND e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+28 THEN 1 ELSE 0 END) AS withdrawn_28,
 MAX(CASE WHEN e.event_type='contract_signed' AND e.event_day>=a.assigned_day AND e.event_day<=a.assigned_day+180 THEN 1 ELSE 0 END) AS contracted_180
 FROM assignments a LEFT JOIN events e USING(assignment_id) GROUP BY a.assignment_id;
