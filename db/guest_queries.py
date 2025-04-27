# db/guest_queries.py
from .connection import get_db_connection
from mysql.connector import Error

def get_all_guests():
    """ Fetches basic guest information. """
    conn = get_db_connection()
    if conn is None: return []
    guests = []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT guest_id, first_name, last_name, email, phone FROM Guests ORDER BY last_name, first_name"
        cursor.execute(query)
        guests = cursor.fetchall()
    except Error as e:
        print(f"Error fetching guests: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return guests

def add_guest_db(first_name, last_name, email, phone, address=None, city=None, country=None, passport=None, dob=None):
    """ Adds a new guest to the database. Returns guest_id or None on failure. """
    conn = get_db_connection()
    if conn is None: return None
    guest_id = None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO Guests
            (first_name, last_name, email, phone, address, city, country, passport_number, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (first_name, last_name, email, phone, address, city, country, passport, dob)
        cursor.execute(query, params)
        conn.commit()
        guest_id = cursor.lastrowid # Get the ID of the inserted row
    except Error as e:
        print(f"Error adding guest: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return guest_id

def find_guest_by_name_db(name_part):
    """ Finds guests whose first or last name contains the search term. """
    conn = get_db_connection()
    if conn is None: return []
    guests = []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT guest_id, first_name, last_name, email, phone
            FROM Guests
            WHERE first_name LIKE %s OR last_name LIKE %s
            ORDER BY last_name, first_name
        """
        search_pattern = f"%{name_part}%"
        cursor.execute(query, (search_pattern, search_pattern))
        guests = cursor.fetchall()
    except Error as e:
        print(f"Error finding guest by name: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return guests

def get_guest_by_id_db(guest_id):
    """ Fetches a single guest by their ID. """
    conn = get_db_connection()
    if conn is None: return None
    guest = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Guests WHERE guest_id = %s"
        cursor.execute(query, (guest_id,))
        guest = cursor.fetchone()
    except Error as e:
        print(f"Error fetching guest by ID: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return guest

# Add update_guest_db, delete_guest_db as needed