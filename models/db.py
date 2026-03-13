import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import Config


def get_db_connection():
    connection = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
    return connection


@contextmanager
def db_cursor(commit=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def initialize_database():
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        phone VARCHAR(20),
        password_hash VARCHAR(255),
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_parking_slots_table = """
    CREATE TABLE IF NOT EXISTS parking_slots (
        id SERIAL PRIMARY KEY,
        slot_number VARCHAR(20) UNIQUE NOT NULL,
        zone VARCHAR(50) NOT NULL,
        slot_type VARCHAR(30) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_reservations_table = """
    CREATE TABLE IF NOT EXISTS reservations (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        vehicle_number VARCHAR(30) NOT NULL,
        reservation_start TIMESTAMP NOT NULL,
        reservation_end TIMESTAMP NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'reserved',
        receipt_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_user
            FOREIGN KEY (user_id)
            REFERENCES users (id)
            ON DELETE CASCADE,
        CONSTRAINT fk_slot
            FOREIGN KEY (slot_id)
            REFERENCES parking_slots (id)
            ON DELETE CASCADE,
        CONSTRAINT valid_time_range
            CHECK (reservation_end > reservation_start)
    );
    """

    create_notifications_log_table = """
    CREATE TABLE IF NOT EXISTS notifications_log (
        id SERIAL PRIMARY KEY,
        reservation_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        channel VARCHAR(50) DEFAULT 'SNS',
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_reservation
            FOREIGN KEY (reservation_id)
            REFERENCES reservations (id)
            ON DELETE CASCADE
    );
    """

    alter_users_queries = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;"
    ]

    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_slots_status ON parking_slots(status);",
        "CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_reservations_slot_id ON reservations(slot_id);",
        "CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);",
        "CREATE INDEX IF NOT EXISTS idx_reservations_start_end ON reservations(reservation_start, reservation_end);"
    ]

    with db_cursor(commit=True) as cursor:
        cursor.execute(create_users_table)
        cursor.execute(create_parking_slots_table)
        cursor.execute(create_reservations_table)
        cursor.execute(create_notifications_log_table)

        for query in alter_users_queries:
            cursor.execute(query)

        for index_query in create_indexes:
            cursor.execute(index_query)