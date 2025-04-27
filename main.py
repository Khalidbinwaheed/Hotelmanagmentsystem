# main.py
import tkinter as tk
from gui.main_window import HotelApp # Import the main app window class
from db.connection import get_db_connection # Import to test connection early

def main():
    # Optional: Test DB connection on startup
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("Successfully connected to the database.")
        conn.close()
    else:
        print("CRITICAL: Failed to connect to the database. Application might not work correctly.")
        # You might want to show an error message and exit if connection fails critically
        # messagebox.showerror("Database Error", "Cannot connect to database. Exiting.")
        # return # Exit if connection is mandatory

    # Create and run the Tkinter application
    app = HotelApp()
    app.mainloop()

if __name__ == "__main__":
    main()