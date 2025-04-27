# gui/checkinout_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

# Use relative imports for DB functions
from ..db.reservation_queries import find_reservation_for_checkin_db, find_reservation_for_checkout_db, update_reservation_status_db
from ..db.room_queries import update_room_status_db # Needed if checkout marks for maintenance


class CheckInOutFrame(ttk.Frame):
    """Frame for handling Check-in and Check-out."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1) # Allow content to center/expand

        title_label = ttk.Label(self, text="Check-in / Check-out", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(10, 20))

        # --- Input Area ---
        input_frame = ttk.LabelFrame(self, text="Find Reservation", padding=15)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky='ew')
        input_frame.columnconfigure(1, weight=1)

        # Combined search field
        ttk.Label(input_frame, text="Search (Guest Name / Room No.):").grid(row=0, column=0, sticky="w", pady=5, padx=(0,5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(input_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=0, column=1, sticky="ew", pady=5)
        search_entry.bind("<Return>", self.auto_find_action) # Allow Enter key

        # Optional: Separate fields if preferred
        # ttk.Label(input_frame, text="Guest Name / Booking ID:").grid(row=0, column=0, sticky="w", pady=5)
        # self.checkin_search_var = tk.StringVar()
        # checkin_search_entry = ttk.Entry(input_frame, textvariable=self.checkin_search_var, width=30)
        # checkin_search_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        # ttk.Label(input_frame, text="Room Number:").grid(row=1, column=0, sticky="w", pady=5)
        # self.checkout_search_var = tk.StringVar()
        # checkout_search_entry = ttk.Entry(input_frame, textvariable=self.checkout_search_var, width=15)
        # checkout_search_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)


        # --- Found Reservation Display ---
        result_frame = ttk.LabelFrame(self, text="Reservation Details", padding=15)
        result_frame.grid(row=2, column=0, padx=20, pady=10, sticky='ew')
        result_frame.columnconfigure(1, weight=1)

        self.result_guest_var = tk.StringVar(value="Guest: -")
        ttk.Label(result_frame, textvariable=self.result_guest_var).grid(row=0, column=0, columnspan=2, sticky='w', pady=2)

        self.result_room_var = tk.StringVar(value="Room: -")
        ttk.Label(result_frame, textvariable=self.result_room_var).grid(row=1, column=0, sticky='w', pady=2)

        self.result_dates_var = tk.StringVar(value="Dates: -")
        ttk.Label(result_frame, textvariable=self.result_dates_var).grid(row=1, column=1, sticky='w', pady=2) # Example layout

        self.result_status_var = tk.StringVar(value="Status: -")
        ttk.Label(result_frame, textvariable=self.result_status_var, font=('Helvetica', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)

        self.current_reservation_id = None # Store ID of found reservation


        # --- Action Buttons ---
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=3, column=0, pady=20)

        self.checkin_btn = ttk.Button(button_frame, text="Perform Check-in", command=self.perform_checkin, state=tk.DISABLED)
        self.checkin_btn.pack(side=tk.LEFT, padx=15)

        self.checkout_btn = ttk.Button(button_frame, text="Perform Check-out", command=self.perform_checkout, state=tk.DISABLED)
        self.checkout_btn.pack(side=tk.LEFT, padx=15)

        # Add a button to clear search results
        clear_btn = ttk.Button(button_frame, text="Clear Search", command=self.clear_search)
        clear_btn.pack(side=tk.LEFT, padx=15)


    def auto_find_action(self, event=None):
        """Tries to find reservation for check-in or check-out based on input."""
        search_key = self.search_var.get().strip()
        if not search_key:
            self.clear_results()
            return

        self.controller.update_status(f"Searching for '{search_key}'...")
        self.clear_results() # Clear previous results

        # Try finding for check-in first (more common search includes names)
        reservation_ci = find_reservation_for_checkin_db(search_key)
        if reservation_ci:
            self.display_reservation_details(reservation_ci, action="checkin")
            self.controller.update_status(f"Found reservation for check-in: Room {reservation_ci['room_number']}")
            return # Found for check-in, stop searching

        # If not found for check-in, try finding for check-out (usually by room number)
        reservation_co = find_reservation_for_checkout_db(search_key) # Assume search_key might be room num
        if reservation_co:
            self.display_reservation_details(reservation_co, action="checkout")
            self.controller.update_status(f"Found reservation for check-out: Room {reservation_co['room_number']}")
            return # Found for check-out

        # If not found for either
        messagebox.showinfo("Not Found", f"No matching reservation found for check-in today or current check-out for '{search_key}'.")
        self.controller.update_status(f"No matching reservation found for '{search_key}'.")


    def display_reservation_details(self, reservation_data, action):
        """Updates the result frame with details and enables appropriate button."""
        self.current_reservation_id = reservation_data['reservation_id']
        guest_name = f"{reservation_data['first_name']} {reservation_data['last_name']}"
        room_num = reservation_data['room_number']

        self.result_guest_var.set(f"Guest: {guest_name} (ID: {reservation_data['guest_id']})")
        self.result_room_var.set(f"Room: {room_num}")
        # Fetch full reservation details if needed for dates (find_... functions only return limited info)
        # self.result_dates_var.set(f"Dates: {reservation_data['check_in_date']} to {reservation_data['check_out_date']}")
        self.result_dates_var.set("Dates: Check DB for full details") # Placeholder

        if action == "checkin":
            self.result_status_var.set("Status: Confirmed (Ready for Check-in)")
            self.checkin_btn.config(state=tk.NORMAL)
            self.checkout_btn.config(state=tk.DISABLED)
        elif action == "checkout":
            self.result_status_var.set("Status: Checked-in (Ready for Check-out)")
            self.checkin_btn.config(state=tk.DISABLED)
            self.checkout_btn.config(state=tk.NORMAL)


    def clear_results(self):
        """Clears the reservation details display and disables buttons."""
        self.result_guest_var.set("Guest: -")
        self.result_room_var.set("Room: -")
        self.result_dates_var.set("Dates: -")
        self.result_status_var.set("Status: -")
        self.current_reservation_id = None
        self.checkin_btn.config(state=tk.DISABLED)
        self.checkout_btn.config(state=tk.DISABLED)

    def clear_search(self):
        """Clears search input and results."""
        self.search_var.set("")
        self.clear_results()
        self.controller.update_status("Check-in/out search cleared.")


    def perform_checkin(self):
        """Performs check-in for the displayed reservation."""
        if self.current_reservation_id is None:
            messagebox.showerror("Error", "No reservation selected for check-in.")
            return

        guest_name = self.result_guest_var.get().split(' (ID:')[0] # Get guest name for confirm message
        if messagebox.askyesno("Confirm Check-in", f"Check in {guest_name} for Reservation ID {self.current_reservation_id}?"):
            self.controller.update_status(f"Processing check-in for ID {self.current_reservation_id}...")
            success = update_reservation_status_db(self.current_reservation_id, 'checked-in')

            if success:
                messagebox.showinfo("Check-in Complete", f"Reservation {self.current_reservation_id} checked in successfully.")
                self.controller.update_status(f"Reservation {self.current_reservation_id} checked in.")
                self.clear_results() # Clear the details after action
                self.search_var.set("") # Clear search bar too
                # Optionally refresh other views
                self.controller.show_frame("RoomManagementFrame") # Go to rooms view to see change
            else:
                messagebox.showerror("Database Error", "Failed to update reservation status for check-in.")
                self.controller.update_status(f"Failed check-in for ID {self.current_reservation_id}.")


    def perform_checkout(self):
        """Performs check-out for the displayed reservation."""
        if self.current_reservation_id is None:
            messagebox.showerror("Error", "No reservation selected for check-out.")
            return

        guest_name = self.result_guest_var.get().split(' (ID:')[0]
        room_num = self.result_room_var.get().replace("Room: ", "")

        # --- Billing Placeholder ---
        # In a real app, calculate the bill here based on room price, services, payments etc.
        # bill_amount = calculate_bill(self.current_reservation_id)
        # confirm_msg = f"Check out {guest_name} (Room {room_num})?\n\nFinal Bill: ${bill_amount:.2f}\n(Billing details not fully implemented)"
        confirm_msg = f"Check out {guest_name} (Room {room_num}) for Reservation ID {self.current_reservation_id}?\n\n(Billing calculation not implemented)"
        # --- End Placeholder ---

        if messagebox.askyesno("Confirm Check-out", confirm_msg):
            self.controller.update_status(f"Processing check-out for ID {self.current_reservation_id}...")

            # Update reservation status to checked-out
            success_res = update_reservation_status_db(self.current_reservation_id, 'checked-out')

            if success_res:
                 # Room status update happens within update_reservation_status_db now
                 messagebox.showinfo("Check-out Complete", f"Reservation {self.current_reservation_id} checked out successfully. Room marked for cleaning.")
                 self.controller.update_status(f"Reservation {self.current_reservation_id} checked out.")
                 self.clear_results()
                 self.search_var.set("")
                 # Optionally refresh other views
                 self.controller.show_frame("RoomManagementFrame")
            else:
                messagebox.showerror("Database Error", "Failed to update reservation or room status for check-out.")
                self.controller.update_status(f"Failed check-out for ID {self.current_reservation_id}.")

    def refresh_data(self):
        """Called when the frame is shown. Clears previous search."""
        self.clear_search()