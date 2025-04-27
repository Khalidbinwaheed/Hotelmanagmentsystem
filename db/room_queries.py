# db/room_queries.py
from .connection import get_db_connection
from mysql.connector import Error

def get_all_rooms_with_details():
    """ Fetches room number, type name, status, price, floor. """
    conn = get_db_connection()
    if conn is None: return []
    rooms = []
    try:
        cursor = conn.cursor(dictionary=True) # Return rows as dictionaries
        query = """
            SELECT
                r.room_id, r.room_number, rt.type_name, rt.base_price,
                r.floor_number,
                CASE
                    WHEN r.maintenance_status = TRUE THEN 'Maintenance'
                    WHEN r.availability = TRUE THEN 'Available'
                    ELSE 'Occupied' -- We'll update this based on Reservations later
                END AS status
            FROM Rooms r
            JOIN RoomTypes rt ON r.room_type_id = rt.room_type_id
            ORDER BY r.room_number
        """
        cursor.execute(query)
        rooms = cursor.fetchall()

        # --- Refine Status based on Reservations ---
        # This is more complex and might be better done with a more advanced query
        # or separate logic, but here's a basic idea:
        query_reservations = """
            SELECT room_id FROM Reservations
            WHERE CURDATE() BETWEEN check_in_date AND check_out_date
            AND status IN ('checked-in', 'confirmed')
        """
        cursor.execute(query_reservations)
        occupied_rooms = {row['room_id'] for row in cursor.fetchall()}

        for room in rooms:
            if room['room_id'] in occupied_rooms and room['status'] != 'Maintenance':
                room['status'] = 'Occupied'
            elif room['status'] != 'Maintenance' and room['room_id'] not in occupied_rooms :
                 room['status'] = 'Available' # Ensure it's available if not maint/occupied

    except Error as e:
        print(f"Error fetching rooms: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return rooms

def update_room_status_db(room_id, availability=None, maintenance=None):
    """ Updates room availability or maintenance status in DB. """
    if availability is None and maintenance is None:
        return False # Nothing to update

    conn = get_db_connection()
    if conn is None: return False
    success = False
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        if availability is not None:
            updates.append("availability = %s")
            params.append(bool(availability))
        if maintenance is not None:
            updates.append("maintenance_status = %s")
            params.append(bool(maintenance))

        query = f"UPDATE Rooms SET {', '.join(updates)} WHERE room_id = %s"
        params.append(room_id)

        cursor.execute(query, tuple(params))
        conn.commit()
        success = cursor.rowcount > 0 # Check if any row was updated
    except Error as e:
        print(f"Error updating room status: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return success

def get_available_rooms_for_booking(check_in, check_out):
     """ Finds rooms available between given dates. """
     conn = get_db_connection()
     if conn is None: return []
     available_rooms = []
     try:
         cursor = conn.cursor(dictionary=True)
         # Find rooms that DO NOT have an overlapping reservation
         query = """
            SELECT r.room_id, r.room_number, rt.type_name, rt.base_price
            FROM Rooms r
            JOIN RoomTypes rt ON r.room_type_id = rt.room_type_id
            WHERE r.maintenance_status = FALSE AND r.room_id NOT IN (
                SELECT res.room_id
                FROM Reservations res
                WHERE res.status IN ('confirmed', 'checked-in')
                  AND (
                    (res.check_in_date <= %s AND res.check_out_date > %s) -- Overlaps start
                    OR (res.check_in_date < %s AND res.check_out_date >= %s) -- Overlaps end
                    OR (res.check_in_date >= %s AND res.check_out_date <= %s) -- Fully contained
                  )
            )
            ORDER BY r.room_number;
         """
         # Parameters: check_out, check_in, check_out, check_in, check_in, check_out
         cursor.execute(query, (check_out, check_in, check_out, check_in, check_in, check_out))
         available_rooms = cursor.fetchall()
     except Error as e:
         print(f"Error fetching available rooms: {e}")
     finally:
         if conn.is_connected():
            cursor.close()
            conn.close()
     return available_rooms

# Add functions for RoomTypes if needed (e.g., get_all_room_types)