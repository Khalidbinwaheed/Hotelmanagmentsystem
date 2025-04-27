# db/reservation_queries.py
from .connection import get_db_connection
from mysql.connector import Error
from datetime import date

def add_reservation_db(guest_id, room_id, check_in, check_out, adults=1, children=0, requests=None):
    """ Adds a new reservation. Returns reservation_id or None. """
    conn = get_db_connection()
    if conn is None: return None
    reservation_id = None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO Reservations
            (guest_id, room_id, check_in_date, check_out_date, adults, children, special_requests, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed')
        """
        params = (guest_id, room_id, check_in, check_out, adults, children, requests)
        cursor.execute(query, params)

        # --- IMPORTANT: Update room availability ---
        # This is a simplified approach. A robust system might use triggers
        # or check dates more carefully. We assume check-in makes it unavailable.
        # However, the room should ONLY become unavailable on check-in.
        # This logic is better handled during the check-in process itself.
        # Let's skip direct availability update here, rely on check-in/out logic.
        # query_update_room = "UPDATE Rooms SET availability = FALSE WHERE room_id = %s"
        # cursor.execute(query_update_room, (room_id,))
        # ---

        conn.commit()
        reservation_id = cursor.lastrowid
    except Error as e:
        print(f"Error adding reservation: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return reservation_id

def update_reservation_status_db(reservation_id, new_status):
    """ Updates the status of a reservation ('cancelled', 'checked-in', 'checked-out'). """
    conn = get_db_connection()
    if conn is None: return False
    success = False
    room_id = None # To potentially update room status
    try:
        cursor = conn.cursor(dictionary=True) # Use dictionary cursor to get room_id

        # Get room_id associated with reservation first
        cursor.execute("SELECT room_id FROM Reservations WHERE reservation_id = %s", (reservation_id,))
        res_data = cursor.fetchone()
        if not res_data:
            print(f"Error: Reservation ID {reservation_id} not found.")
            return False
        room_id = res_data['room_id']

        # Update reservation status
        query = "UPDATE Reservations SET status = %s WHERE reservation_id = %s"
        cursor.execute(query, (new_status, reservation_id))

        # Update room availability based on the new status
        if new_status == 'checked-in':
            # Mark room as unavailable (occupied)
            query_room = "UPDATE Rooms SET availability = FALSE WHERE room_id = %s"
            cursor.execute(query_room, (room_id,))
        elif new_status in ['checked-out', 'cancelled']:
             # Mark room as available (simplistic, might need cleaning status)
             # More accurately, check-out should perhaps mark it 'Maintenance' or trigger cleaning workflow.
             # For now, just make it available if not cancelled/checked-out.
             query_room = "UPDATE Rooms SET availability = TRUE, maintenance_status = FALSE WHERE room_id = %s" # Reset maintenance too for simplicity
             if new_status == 'checked-out':
                 query_room = "UPDATE Rooms SET availability = FALSE, maintenance_status = TRUE WHERE room_id = %s" # Mark for cleaning
             cursor.execute(query_room, (room_id,))


        conn.commit()
        success = cursor.rowcount > 0 # Check if reservation status update was successful
    except Error as e:
        print(f"Error updating reservation status: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return success


def find_reservation_for_checkin_db(search_key):
    """ Finds a 'confirmed' reservation matching guest name or room number for today's check-in. """
    conn = get_db_connection()
    if conn is None: return None
    reservation = None
    try:
        cursor = conn.cursor(dictionary=True)
        today = date.today().isoformat()
        query = """
            SELECT res.reservation_id, res.room_id, r.room_number, g.guest_id, g.first_name, g.last_name
            FROM Reservations res
            JOIN Guests g ON res.guest_id = g.guest_id
            JOIN Rooms r ON res.room_id = r.room_id
            WHERE res.check_in_date = %s AND res.status = 'confirmed'
              AND (r.room_number = %s OR g.first_name LIKE %s OR g.last_name LIKE %s)
            LIMIT 1
        """
        search_pattern = f"%{search_key}%"
        cursor.execute(query, (today, search_key, search_pattern, search_pattern))
        reservation = cursor.fetchone()
    except Error as e:
        print(f"Error finding reservation for check-in: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return reservation

def find_reservation_for_checkout_db(room_number):
    """ Finds a 'checked-in' reservation matching the room number. """
    conn = get_db_connection()
    if conn is None: return None
    reservation = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT res.reservation_id, res.room_id, r.room_number, g.guest_id, g.first_name, g.last_name
            FROM Reservations res
            JOIN Guests g ON res.guest_id = g.guest_id
            JOIN Rooms r ON res.room_id = r.room_id
            WHERE r.room_number = %s AND res.status = 'checked-in'
            LIMIT 1
        """
        cursor.execute(query, (room_number,))
        reservation = cursor.fetchone()
    except Error as e:
        print(f"Error finding reservation for check-out: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return reservation

# Add get_all_reservations, etc. as needed