PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS booking_events (
  event_id        INTEGER PRIMARY KEY,
  booking_id      INTEGER NOT NULL,
  event_type      TEXT NOT NULL,          
  old_status      TEXT,
  new_status      TEXT,
  old_values      TEXT,
  new_values      TEXT,
  event_note      TEXT,
  occurred_at_utc TEXT NOT NULL DEFAULT (datetime('now')),
  actor           TEXT,                    
  FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_booking_events_booking_time
  ON booking_events(booking_id, occurred_at_utc);



DROP TRIGGER IF EXISTS trg_bookings_ai_history;
DROP TRIGGER IF EXISTS trg_bookings_au_history;
DROP TRIGGER IF EXISTS trg_bookings_bd_history;

CREATE TRIGGER trg_bookings_ai_history
AFTER INSERT ON bookings
BEGIN
  INSERT INTO booking_events (booking_id, event_type, new_status, new_values, actor)
  VALUES (NEW.booking_id, 'CREATED', NEW.status, NULL, 'system');
END;

CREATE TRIGGER trg_bookings_au_history
AFTER UPDATE ON bookings
BEGIN
  INSERT INTO booking_events (
    booking_id, event_type, old_status, new_status, old_values, new_values, actor
  ) VALUES (
    NEW.booking_id,
    CASE WHEN (OLD.status IS NOT NEW.status AND OLD.status != NEW.status)
         THEN 'STATUS_CHANGE' ELSE 'UPDATED' END,
    OLD.status, NEW.status, NULL, NULL, 'system'
  );
END;

CREATE TRIGGER trg_bookings_bd_history
BEFORE DELETE ON bookings
BEGIN
  INSERT INTO booking_events (booking_id, event_type, old_status, new_values, actor)
  VALUES (OLD.booking_id, 'DELETED', OLD.status, NULL, 'system');
END;
