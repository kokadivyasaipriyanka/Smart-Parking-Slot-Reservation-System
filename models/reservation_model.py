from models.db import db_cursor


class ReservationModel:
    VALID_STATUSES = {"reserved", "cancelled", "completed", "expired"}

    @staticmethod
    def create_reservation(
        user_id,
        slot_id,
        vehicle_number,
        reservation_start,
        reservation_end,
        status="reserved",
        receipt_url=None
    ):
        """
        Create a reservation and return the inserted row.
        """
        if status not in ReservationModel.VALID_STATUSES:
            raise ValueError(f"Invalid reservation status: {status}")

        query = """
        INSERT INTO reservations (
            user_id,
            slot_id,
            vehicle_number,
            reservation_start,
            reservation_end,
            status,
            receipt_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    slot_id,
                    vehicle_number,
                    reservation_start,
                    reservation_end,
                    status,
                    receipt_url
                )
            )
            return cursor.fetchone()

    @staticmethod
    def get_all_reservations():
        """
        Return all reservations with joined user and slot details.
        """
        query = """
        SELECT
            r.*,
            u.full_name AS user_name,
            u.email AS user_email,
            s.slot_number,
            s.zone,
            s.slot_type
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking_slots s ON r.slot_id = s.id
        ORDER BY r.id DESC;
        """
        with db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_reservation_by_id(reservation_id):
        """
        Return one reservation by ID with joined details.
        """
        query = """
        SELECT
            r.*,
            u.full_name AS user_name,
            u.email AS user_email,
            s.slot_number,
            s.zone,
            s.slot_type
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking_slots s ON r.slot_id = s.id
        WHERE r.id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (reservation_id,))
            return cursor.fetchone()

    @staticmethod
    def get_reservations_by_user(user_id):
        """
        Return all reservations for a specific user with joined details.
        """
        query = """
        SELECT
            r.*,
            u.full_name AS user_name,
            u.email AS user_email,
            s.slot_number,
            s.zone,
            s.slot_type
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking_slots s ON r.slot_id = s.id
        WHERE r.user_id = %s
        ORDER BY r.id DESC;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_reservations_by_slot(slot_id):
        """
        Return all reservations for a slot.
        """
        query = """
        SELECT
            r.*,
            u.full_name AS user_name,
            u.email AS user_email,
            s.slot_number,
            s.zone,
            s.slot_type
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking_slots s ON r.slot_id = s.id
        WHERE r.slot_id = %s
        ORDER BY r.reservation_start DESC;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (slot_id,))
            return cursor.fetchall()

    @staticmethod
    def get_active_reservations_by_slot(slot_id):
        """
        Return active reservations for a slot.
        Active means status='reserved'.
        """
        query = """
        SELECT *
        FROM reservations
        WHERE slot_id = %s
          AND status = 'reserved'
        ORDER BY reservation_start ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (slot_id,))
            return cursor.fetchall()

    @staticmethod
    def update_reservation(
        reservation_id,
        user_id,
        slot_id,
        vehicle_number,
        reservation_start,
        reservation_end,
        status,
        receipt_url=None
    ):
        """
        Update a reservation and return the updated row.
        """
        if status not in ReservationModel.VALID_STATUSES:
            raise ValueError(f"Invalid reservation status: {status}")

        query = """
        UPDATE reservations
        SET user_id = %s,
            slot_id = %s,
            vehicle_number = %s,
            reservation_start = %s,
            reservation_end = %s,
            status = %s,
            receipt_url = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    slot_id,
                    vehicle_number,
                    reservation_start,
                    reservation_end,
                    status,
                    receipt_url,
                    reservation_id
                )
            )
            return cursor.fetchone()

    @staticmethod
    def update_reservation_status(reservation_id, status):
        """
        Update only reservation status and return updated row.
        """
        if status not in ReservationModel.VALID_STATUSES:
            raise ValueError(f"Invalid reservation status: {status}")

        query = """
        UPDATE reservations
        SET status = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (status, reservation_id))
            return cursor.fetchone()

    @staticmethod
    def update_receipt_url(reservation_id, receipt_url):
        """
        Update only the receipt URL for a reservation.
        """
        query = """
        UPDATE reservations
        SET receipt_url = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (receipt_url, reservation_id))
            return cursor.fetchone()

    @staticmethod
    def delete_reservation(reservation_id):
        """
        Delete a reservation.
        Returns True if deleted, otherwise False.
        """
        query = """
        DELETE FROM reservations
        WHERE id = %s
        RETURNING id;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (reservation_id,))
            deleted_row = cursor.fetchone()
            return deleted_row is not None

    @staticmethod
    def reservation_exists(reservation_id):
        """
        Check whether a reservation exists.
        """
        query = """
        SELECT 1
        FROM reservations
        WHERE id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (reservation_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def get_expired_active_reservations():
        """
        Return all active reservations whose end time has passed.
        Useful for Lambda scheduled tasks.
        """
        query = """
        SELECT *
        FROM reservations
        WHERE status = 'reserved'
          AND reservation_end < CURRENT_TIMESTAMP
        ORDER BY reservation_end ASC;
        """
        with db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def log_notification(reservation_id, message, channel="SNS"):
        """
        Store a notification log entry.
        """
        query = """
        INSERT INTO notifications_log (reservation_id, message, channel)
        VALUES (%s, %s, %s)
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (reservation_id, message, channel))
            return cursor.fetchone()