from models.db import db_cursor


class SlotModel:
    VALID_STATUSES = {"available", "reserved", "occupied", "maintenance"}

    @staticmethod
    def create_slot(slot_number, zone, slot_type, status="available"):
        """
        Create a parking slot and return the inserted row.
        """
        if status not in SlotModel.VALID_STATUSES:
            raise ValueError(f"Invalid slot status: {status}")

        query = """
        INSERT INTO parking_slots (slot_number, zone, slot_type, status)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (slot_number, zone, slot_type, status))
            return cursor.fetchone()

    @staticmethod
    def get_all_slots():
        """
        Return all parking slots ordered by slot number.
        """
        query = """
        SELECT *
        FROM parking_slots
        ORDER BY slot_number ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_slot_by_id(slot_id):
        """
        Return one slot by ID or None.
        """
        query = """
        SELECT *
        FROM parking_slots
        WHERE id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (slot_id,))
            return cursor.fetchone()

    @staticmethod
    def get_slot_by_number(slot_number):
        """
        Return one slot by slot number or None.
        """
        query = """
        SELECT *
        FROM parking_slots
        WHERE slot_number = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (slot_number,))
            return cursor.fetchone()

    @staticmethod
    def get_slots_by_status(status="available"):
        """
        Return slots matching a specific status.
        """
        query = """
        SELECT *
        FROM parking_slots
        WHERE status = %s
        ORDER BY slot_number ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (status,))
            return cursor.fetchall()

    @staticmethod
    def get_slots_by_zone(zone):
        """
        Return all slots in a specific zone.
        """
        query = """
        SELECT *
        FROM parking_slots
        WHERE zone = %s
        ORDER BY slot_number ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (zone,))
            return cursor.fetchall()

    @staticmethod
    def get_available_slots():
        """
        Return all currently available slots.
        """
        query = """
        SELECT *
        FROM parking_slots
        WHERE status = 'available'
        ORDER BY slot_number ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def update_slot(slot_id, slot_number, zone, slot_type, status):
        """
        Update full slot details and return the updated row.
        """
        if status not in SlotModel.VALID_STATUSES:
            raise ValueError(f"Invalid slot status: {status}")

        query = """
        UPDATE parking_slots
        SET slot_number = %s,
            zone = %s,
            slot_type = %s,
            status = %s
        WHERE id = %s
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (slot_number, zone, slot_type, status, slot_id))
            return cursor.fetchone()

    @staticmethod
    def update_slot_status(slot_id, status):
        """
        Update only slot status and return updated row.
        """
        if status not in SlotModel.VALID_STATUSES:
            raise ValueError(f"Invalid slot status: {status}")

        query = """
        UPDATE parking_slots
        SET status = %s
        WHERE id = %s
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (status, slot_id))
            return cursor.fetchone()

    @staticmethod
    def delete_slot(slot_id):
        """
        Delete a parking slot by ID.
        Returns True if deleted, otherwise False.
        """
        query = """
        DELETE FROM parking_slots
        WHERE id = %s
        RETURNING id;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (slot_id,))
            deleted_row = cursor.fetchone()
            return deleted_row is not None

    @staticmethod
    def slot_exists(slot_id):
        """
        Check whether a slot exists.
        """
        query = """
        SELECT 1
        FROM parking_slots
        WHERE id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (slot_id,))
            return cursor.fetchone() is not None