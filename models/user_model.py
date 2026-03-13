from werkzeug.security import generate_password_hash, check_password_hash
from models.db import db_cursor


class UserModel:
    @staticmethod
    def create_user(full_name, email, phone=None, password=None, is_admin=False):
        password_hash = generate_password_hash(password) if password else None

        query = """
        INSERT INTO users (full_name, email, phone, password_hash, is_admin)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (full_name, email, phone, password_hash, is_admin))
            return cursor.fetchone()

    @staticmethod
    def get_all_users():
        query = """
        SELECT *
        FROM users
        ORDER BY id DESC;
        """
        with db_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_user_by_id(user_id):
        query = """
        SELECT *
        FROM users
        WHERE id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_email(email):
        query = """
        SELECT *
        FROM users
        WHERE email = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (email,))
            return cursor.fetchone()

    @staticmethod
    def authenticate_user(email, password):
        user = UserModel.get_user_by_email(email)
        if not user or not user.get("password_hash"):
            return None

        if check_password_hash(user["password_hash"], password):
            return user
        return None

    @staticmethod
    def update_user(user_id, full_name, email, phone=None, password=None, is_admin=False):
        if password:
            query = """
            UPDATE users
            SET full_name = %s,
                email = %s,
                phone = %s,
                password_hash = %s,
                is_admin = %s
            WHERE id = %s
            RETURNING *;
            """
            password_hash = generate_password_hash(password)
            params = (full_name, email, phone, password_hash, is_admin, user_id)
        else:
            query = """
            UPDATE users
            SET full_name = %s,
                email = %s,
                phone = %s,
                is_admin = %s
            WHERE id = %s
            RETURNING *;
            """
            params = (full_name, email, phone, is_admin, user_id)

        with db_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    @staticmethod
    def delete_user(user_id):
        query = """
        DELETE FROM users
        WHERE id = %s
        RETURNING id;
        """
        with db_cursor(commit=True) as cursor:
            cursor.execute(query, (user_id,))
            deleted_row = cursor.fetchone()
            return deleted_row is not None

    @staticmethod
    def user_exists(user_id):
        query = """
        SELECT 1
        FROM users
        WHERE id = %s;
        """
        with db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def ensure_default_admin(full_name, email, password, phone=None):
        existing_user = UserModel.get_user_by_email(email)

        if existing_user:
            if not existing_user.get("is_admin") or not existing_user.get("password_hash"):
                return UserModel.update_user(
                    user_id=existing_user["id"],
                    full_name=existing_user["full_name"] or full_name,
                    email=existing_user["email"],
                    phone=existing_user.get("phone") or phone,
                    password=password,
                    is_admin=True
                )
            return existing_user

        return UserModel.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password=password,
            is_admin=True
        )