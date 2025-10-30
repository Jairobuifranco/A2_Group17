import sqlite3, pathlib, sys


FORCE_TABLE  = "order"   
FORCE_PK     = None      
FORCE_STATUS = None      


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

# Find the DB file
CANDIDATES = [pathlib.Path("instance/sitedata.sqlite"), pathlib.Path("sitedata.sqlite")]
DB_PATH = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])

def table_info(con, table):
    
    return con.execute(f"PRAGMA table_info({q(table)})").fetchall()  

def find_pk(cols):
    for _, name, _type, _nn, _dflt, pkflag in cols:
        if pkflag == 1:
            return name
    return None

def find_status(cols):
    # Try common names
    wanted = {"status","order_status","booking_status","state"}
    lower_map = {c[1].lower(): c[1] for c in cols}
    for w in wanted:
        if w in lower_map:
            return lower_map[w]
    return None

with sqlite3.connect(DB_PATH) as con:
    con.execute("PRAGMA foreign_keys = ON;")

    table = FORCE_TABLE
    cols = table_info(con, table)
    if not cols:
        print(f"❌ Could not read columns for table {table}. Is it present?")
        sys.exit(1)

    pk = FORCE_PK or find_pk(cols) or "rowid"
    status_col = FORCE_STATUS or find_status(cols)

    print(f"DB: {DB_PATH}")
    print(f"Table: {table}")
    print(f"Primary key: {pk}")
    print(f"Status column: {status_col or '(none – will log without statuses)'}")

    
    con.executescript(f"""
    DROP TRIGGER IF EXISTS trg_booking_events_ai_history;
    DROP TRIGGER IF EXISTS trg_booking_events_au_history;
    DROP TRIGGER IF EXISTS trg_booking_events_bd_history;
    DROP TRIGGER IF EXISTS trg_{table}_ai_history;
    DROP TRIGGER IF EXISTS trg_{table}_au_history;
    DROP TRIGGER IF EXISTS trg_{table}_bd_history;
    """)

    
    con.executescript("""
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
      actor           TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_booking_events_booking_time
      ON booking_events(booking_id, occurred_at_utc);
    """)

    t = q(table)
    pkq = q(pk)

    if status_col:
        scq = q(status_col)
        con.executescript(f"""
        CREATE TRIGGER trg_{table}_ai_history
        AFTER INSERT ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, new_status, new_values, actor)
          VALUES (NEW.{pkq}, 'CREATED', NEW.{scq}, NULL, 'system');
        END;

        CREATE TRIGGER trg_{table}_au_history
        AFTER UPDATE ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, old_status, new_status, old_values, new_values, actor)
          VALUES (
            NEW.{pkq},
            CASE WHEN (OLD.{scq} IS NOT NEW.{scq} AND OLD.{scq} != NEW.{scq})
                 THEN 'STATUS_CHANGE' ELSE 'UPDATED' END,
            OLD.{scq}, NEW.{scq}, NULL, NULL, 'system'
          );
        END;

        CREATE TRIGGER trg_{table}_bd_history
        BEFORE DELETE ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, old_status, new_values, actor)
          VALUES (OLD.{pkq}, 'DELETED', OLD.{scq}, NULL, 'system');
        END;
        """)
    else:
        con.executescript(f"""
        CREATE TRIGGER trg_{table}_ai_history
        AFTER INSERT ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, new_values, actor)
          VALUES (NEW.{pkq}, 'CREATED', NULL, 'system');
        END;

        CREATE TRIGGER trg_{table}_au_history
        AFTER UPDATE ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, old_values, new_values, actor)
          VALUES (NEW.{pkq}, 'UPDATED', NULL, NULL, 'system');
        END;

        CREATE TRIGGER trg_{table}_bd_history
        BEFORE DELETE ON {t}
        BEGIN
          INSERT INTO booking_events (booking_id, event_type, new_values, actor)
          VALUES (OLD.{pkq}, 'DELETED', NULL, 'system');
        END;
        """)
    print("✅ Booking history triggers installed.")

