# gui/dashboard_frame.py
import tkinter as tk
from tkinter import ttk
# Use relative imports for DB functions
from ..db.room_queries import get_all_rooms_with_details
# Import other queries as needed (e.g., for guest count, upcoming check-ins)
# from ..db.guest_queries import get_all_guests
# from ..db.reservation_queries import get_upcoming_checkins # Example

class DashboardFrame(ttk.Frame):
    """The initial view showing quick stats and actions."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure grid layout for this frame
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1) # Two main columns

        # Title Label
        label = ttk.Label(self, text="Hotel Dashboard", font=('Helvetica', 16, 'bold'))
        label.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="n")

        # --- Quick Stats Area ---
        stats_frame = ttk.LabelFrame(self, text="Current Status", padding=15)
        stats_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        stats_frame.grid_columnconfigure(1, weight=1) # Let value labels expand if needed

        row_idx = 0
        ttk.Label(stats_frame, text="Available Rooms:", font=('Helvetica', 10)).grid(row=row_idx, column=0, sticky="w", pady=3)
        self.available_rooms_var = tk.StringVar(value="...")
        ttk.Label(stats_frame, textvariable=self.available_rooms_var, font=('Helvetica', 10, 'bold')).grid(row=row_idx, column=1, sticky="w", pady=3)
        row_idx += 1

        ttk.Label(stats_frame, text="Occupied Rooms:", font=('Helvetica', 10)).grid(row=row_idx, column=0, sticky="w", pady=3)
        self.occupied_rooms_var = tk.StringVar(value="...")
        ttk.Label(stats_frame, textvariable=self.occupied_rooms_var, font=('Helvetica', 10, 'bold')).grid(row=row_idx, column=1, sticky="w", pady=3)
        row_idx += 1

        ttk.Label(stats_frame, text="Rooms in Maintenance:", font=('Helvetica', 10)).grid(row=row_idx, column=0, sticky="w", pady=3)
        self.maintenance_rooms_var = tk.StringVar(value="...")
        ttk.Label(stats_frame, textvariable=self.maintenance_rooms_var, font=('Helvetica', 10, 'bold')).grid(row=row_idx, column=1, sticky="w", pady=3)
        row_idx += 1

        # Add more stats as needed (Total Guests, Upcoming Check-ins/outs)
        # ttk.Label(stats_frame, text="Total Guests:").grid(row=row_idx, column=0, sticky="w", pady=2)
        # self.total_guests_var = tk.StringVar(value="...")
        # ttk.Label(stats_frame, textvariable=self.total_guests_var).grid(row=row_idx, column=1, sticky="w", pady=2)
        # row_idx += 1

        # --- Quick Actions Area ---
        actions_frame = ttk.LabelFrame(self, text="Quick Actions", padding=15)
        actions_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        actions_frame.grid_columnconfigure(0, weight=1) # Make button expand

        btn_pady = 8 # Padding between buttons
        book_btn = ttk.Button(actions_frame, text="New Booking",
                              command=lambda: controller.show_frame("BookingFrame"), style="Accent.TButton") # Example style
        book_btn.grid(row=0, column=0, pady=btn_pady, sticky="ew")

        checkin_btn = ttk.Button(actions_frame, text="Check-in / Check-out",
                                 command=lambda: controller.show_frame("CheckInOutFrame"))
        checkin_btn.grid(row=1, column=0, pady=btn_pady, sticky="ew")

        rooms_btn = ttk.Button(actions_frame, text="View Rooms",
                               command=lambda: controller.show_frame("RoomManagementFrame"))
        rooms_btn.grid(row=2, column=0, pady=btn_pady, sticky="ew")

        guests_btn = ttk.Button(actions_frame, text="View Guests",
                                command=lambda: controller.show_frame("GuestManagementFrame"))
        guests_btn.grid(row=3, column=0, pady=btn_pady, sticky="ew")

        # Optional: Add a refresh button for the dashboard itself
        refresh_btn = ttk.Button(self, text="Refresh Dashboard", command=self.refresh_data)
        refresh_btn.grid(row=2, column=0, columnspan=2, pady=(10, 5))

        # Add style for accent button if theme supports it
        controller.style.configure("Accent.TButton", font=('Helvetica', 11, 'bold'), foreground="white", background="#007bff") # Example blue


    def refresh_data(self):
        """Update dashboard stats by fetching data from the database."""
        self.controller.update_status("Refreshing dashboard data...")
        rooms_list = get_all_rooms_with_details() # Fetch current room details
        # guests_list = get_all_guests() # Fetch guests if needed for stats

        if rooms_list is None: # Handle DB error
            self.available_rooms_var.set("Error")
            self.occupied_rooms_var.set("Error")
            self.maintenance_rooms_var.set("Error")
            self.controller.update_status("Error fetching room data for dashboard.")
            return

        # Calculate stats from the fetched list
        available = sum(1 for room in rooms_list if room.get('status') == 'Available')
        occupied = sum(1 for room in rooms_list if room.get('status') == 'Occupied')
        maintenance = sum(1 for room in rooms_list if room.get('status') == 'Maintenance')
        # total_guests = len(guests_list) if guests_list is not None else "Error"

        self.available_rooms_var.set(str(available))
        self.occupied_rooms_var.set(str(occupied))
        self.maintenance_rooms_var.set(str(maintenance))
        # self.total_guests_var.set(str(total_guests))

        self.controller.update_status("Dashboard refreshed.")