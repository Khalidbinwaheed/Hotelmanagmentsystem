# gui/booking_frame.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry # Use the calendar widget
from datetime import date, timedelta, datetime

# Use relative imports for DB functions
from ..db.guest_queries import find_guest_by_name_db, get_guest_by_id_db, add_guest_db
from ..db.room_queries import get_available_rooms_for_booking
from ..db.reservation_queries import add_reservation_db

class BookingFrame(ttk.Frame):
    """Frame for creating a new booking."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_guest_id = None
        self.available_rooms_cache = [] # Cache for available rooms list

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2) # Give more weight to right column
        self.grid_rowconfigure(3, weight=1) # Allow available rooms list to expand

        title = ttk.Label(self, text="New Booking", font=('Helvetica', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        # --- Left Column: Guest and Dates ---
        left_frame = ttk.Frame(self, padding=10)
        left_frame.grid(row=1, column=0, rowspan=3, sticky='nsew', padx=(10, 5))
        left_frame.grid_columnconfigure(1, weight=1)

        # Guest Selection
        guest_lf = ttk.LabelFrame(left_frame, text="Select Guest", padding=10)
        guest_lf.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        guest_lf.grid_columnconfigure(1, weight=1)

        ttk.Label(guest_lf, text="Search Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.guest_search_var = tk.StringVar()
        self.guest_search_entry = ttk.Entry(guest_lf, textvariable=self.guest_search_var, width=25)
        self.guest_search_entry.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        self.guest_search_entry.bind("<KeyRelease>", self.search_guests_for_booking) # Search as user types

        self.guest_combobox = ttk.Combobox(guest_lf, state="readonly", width=35)
        self.guest_combobox.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5, 10), padx=5)
        self.guest_combobox.bind("<<ComboboxSelected>>", self.on_guest_selected)

        self.selected_guest_label = ttk.Label(guest_lf, text="Selected Guest: None", font=('Helvetica', 9, 'italic'))
        self.selected_guest_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=2, padx=5)

        # Add New Guest Button
        add_guest_btn = ttk.Button(guest_lf, text="Add New Guest", command=self.add_new_guest)
        add_guest_btn.grid(row=3, column=0, columnspan=2, pady=5)


        # Date Selection
        dates_lf = ttk.LabelFrame(left_frame, text="Select Dates", padding=10)
        dates_lf.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        dates_lf.grid_columnconfigure(1, weight=1)

        ttk.Label(dates_lf, text="Check-in:").grid(row=0, column=0, sticky="w", pady=5)
        self.checkin_var = tk.StringVar()
        self.checkin_entry = DateEntry(dates_lf, textvariable=self.checkin_var, date_pattern='yyyy-mm-dd',
                                        width=12, background='darkblue', foreground='white', borderwidth=2,
                                        mindate=date.today()) # Prevent past dates
        self.checkin_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        # Set default check-in to today
        self.checkin_entry.set_date(date.today())

        ttk.Label(dates_lf, text="Check-out:").grid(row=1, column=0, sticky="w", pady=5)
        self.checkout_var = tk.StringVar()
        self.checkout_entry = DateEntry(dates_lf, textvariable=self.checkout_var, date_pattern='yyyy-mm-dd',
                                         width=12, background='darkblue', foreground='white', borderwidth=2)
        self.checkout_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        # Set default check-out to tomorrow, mindate based on check-in
        self.checkout_entry.set_date(date.today() + timedelta(days=1))
        self.checkin_entry.bind("<<DateEntrySelected>>", self.update_checkout_mindate)
        self.update_checkout_mindate() # Set initial min date

        # Button to find available rooms for the selected dates
        find_rooms_btn = ttk.Button(dates_lf, text="Find Available Rooms", command=self.find_available_rooms)
        find_rooms_btn.grid(row=2, column=0, columnspan=2, pady=10)


        # Booking Details (Adults/Children/Requests)
        details_lf = ttk.LabelFrame(left_frame, text="Booking Details", padding=10)
        details_lf.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        details_lf.grid_columnconfigure(1, weight=1)

        ttk.Label(details_lf, text="Adults:").grid(row=0, column=0, sticky='w', pady=2)
        self.adults_var = tk.IntVar(value=1)
        adults_spinbox = ttk.Spinbox(details_lf, from_=1, to=10, textvariable=self.adults_var, width=5, wrap=True)
        adults_spinbox.grid(row=0, column=1, sticky='w', pady=2, padx=5)

        ttk.Label(details_lf, text="Children:").grid(row=1, column=0, sticky='w', pady=2)
        self.children_var = tk.IntVar(value=0)
        children_spinbox = ttk.Spinbox(details_lf, from_=0, to=10, textvariable=self.children_var, width=5, wrap=True)
        children_spinbox.grid(row=1, column=1, sticky='w', pady=2, padx=5)

        ttk.Label(details_lf, text="Special Requests:").grid(row=2, column=0, sticky='nw', pady=2)
        self.requests_text = tk.Text(details_lf, height=3, width=30, wrap=tk.WORD)
        self.requests_text.grid(row=2, column=1, sticky='ew', pady=2, padx=5)


        # --- Right Column: Available Rooms ---
        right_frame = ttk.LabelFrame(self, text="Select Available Room", padding=10)
        right_frame.grid(row=1, column=1, rowspan=3, sticky='nsew', padx=(5, 10), pady=(0, 10)) # Extend across rows
        right_frame.grid_rowconfigure(0, weight=1) # Allow listbox to expand
        right_frame.grid_columnconfigure(0, weight=1)

        self.rooms_listbox = tk.Listbox(right_frame, height=15, exportselection=False)
        self.rooms_listbox.grid(row=0, column=0, sticky='nsew', pady=5)
        rooms_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.rooms_listbox.yview)
        rooms_scrollbar.grid(row=0, column=1, sticky='ns', pady=5)
        self.rooms_listbox.config(yscrollcommand=rooms_scrollbar.set)


        # --- Bottom Row: Create Booking Button ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(15, 10))
        submit_button = ttk.Button(button_frame, text="Create Booking", command=self.create_booking, style="Accent.TButton")
        submit_button.pack()


    def update_checkout_mindate(self, event=None):
        """Ensure check-out date is after check-in date."""
        try:
            checkin_date = self.checkin_entry.get_date()
            checkout_min_date = checkin_date + timedelta(days=1)
            self.checkout_entry.config(mindate=checkout_min_date)
            # If current checkout is before new min date, update it
            if self.checkout_entry.get_date() < checkout_min_date:
                self.checkout_entry.set_date(checkout_min_date)
        except Exception as e:
            print(f"Error updating checkout mindate: {e}") # Handle potential date parsing errors


    def search_guests_for_booking(self, event=None):
        """Search guests based on entry and update combobox."""
        search_term = self.guest_search_var.get().strip()
        if len(search_term) < 2: # Don't search for very short strings
            self.guest_combobox['values'] = []
            self.guest_combobox.set('')
            return

        guests = find_guest_by_name_db(search_term)
        if guests:
            guest_display_list = [f"{g['guest_id']}: {g['first_name']} {g['last_name']} ({g.get('email', 'No Email')})" for g in guests]
            self.guest_combobox['values'] = guest_display_list
        else:
            self.guest_combobox['values'] = []
            self.guest_combobox.set('')

    def on_guest_selected(self, event=None):
        """Update selected guest ID and label when combobox selection changes."""
        selection = self.guest_combobox.get()
        if selection:
            try:
                # Extract guest ID from the display string (assuming format "ID: Name (Email)")
                self.selected_guest_id = int(selection.split(':')[0])
                guest_info = get_guest_by_id_db(self.selected_guest_id) # Fetch details to confirm
                if guest_info:
                    display_name = f"{guest_info['first_name']} {guest_info['last_name']}"
                    self.selected_guest_label.config(text=f"Selected Guest: {display_name} (ID: {self.selected_guest_id})")
                else:
                     raise ValueError("Guest not found in DB")
            except (IndexError, ValueError, TypeError) as e:
                print(f"Error parsing guest selection: {e}")
                self.selected_guest_id = None
                self.selected_guest_label.config(text="Selected Guest: Error parsing selection")
        else:
            self.selected_guest_id = None
            self.selected_guest_label.config(text="Selected Guest: None")

    def add_new_guest(self):
        """Simplified guest addition directly from booking form."""
        # This could open a more detailed dialog, but for now use simpledialog
        fname = simpledialog.askstring("New Guest", "Enter First Name:", parent=self)
        if not fname: return
        lname = simpledialog.askstring("New Guest", "Enter Last Name:", parent=self)
        if not lname: return
        email = simpledialog.askstring("New Guest", f"Enter Email for {fname} {lname}:", parent=self)
        phone = simpledialog.askstring("New Guest", f"Enter Phone for {fname} {lname}:", parent=self)
        if not phone:
             messagebox.showwarning("Input Required", "Phone number is required.")
             return

        guest_id = add_guest_db(
            first_name=fname.strip(), last_name=lname.strip(),
            email=email.strip() if email else None, phone=phone.strip()
        )

        if guest_id:
            messagebox.showinfo("Guest Added", f"Guest '{fname} {lname}' added (ID: {guest_id}). You can now search for them.")
            # Optionally auto-select the newly added guest:
            self.guest_search_var.set(f"{fname} {lname}")
            self.search_guests_for_booking()
            # Try to find the exact match in the combobox and set it
            for item in self.guest_combobox['values']:
                if item.startswith(f"{guest_id}:"):
                    self.guest_combobox.set(item)
                    self.on_guest_selected()
                    break
        else:
            messagebox.showerror("Error", "Failed to add guest.")


    def find_available_rooms(self):
        """Fetch and display rooms available for the selected dates."""
        try:
            check_in_str = self.checkin_entry.get_date().isoformat()
            check_out_str = self.checkout_entry.get_date().isoformat()
        except Exception as e:
             messagebox.showerror("Date Error", f"Invalid date format selected.\n{e}")
             return

        self.controller.update_status(f"Finding rooms available from {check_in_str} to {check_out_str}...")
        self.rooms_listbox.delete(0, tk.END) # Clear previous list
        self.available_rooms_cache.clear() # Clear cache

        rooms = get_available_rooms_for_booking(check_in_str, check_out_str)

        if rooms is None:
            messagebox.showerror("Database Error", "Could not fetch available rooms.")
            self.controller.update_status("Error finding available rooms.")
            return

        if not rooms:
            messagebox.showinfo("No Rooms", "No rooms are available for the selected dates.")
            self.controller.update_status("No rooms found for selected dates.")
            return

        self.available_rooms_cache = rooms # Store the full room data
        for room in rooms:
            price = room.get('base_price', 0.0)
            display_text = f"Room {room['room_number']} ({room['type_name']}) - ${price:.2f}/night"
            self.rooms_listbox.insert(tk.END, display_text)

        self.controller.update_status(f"Found {len(rooms)} available rooms.")


    def create_booking(self):
        """Validates input and creates the reservation in the database."""
        # 1. Validate Guest Selection
        if self.selected_guest_id is None:
            messagebox.showerror("Input Error", "Please select a guest.")
            return

        # 2. Validate Dates (already somewhat handled by DateEntry)
        try:
            check_in_date = self.checkin_entry.get_date()
            check_out_date = self.checkout_entry.get_date()
            if check_out_date <= check_in_date:
                 messagebox.showerror("Date Error", "Check-out date must be after check-in date.")
                 return
        except Exception as e:
            messagebox.showerror("Date Error", f"Invalid date format: {e}")
            return

        # 3. Validate Room Selection
        selected_indices = self.rooms_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Input Error", "Please select an available room from the list.")
            return
        selected_room_index = selected_indices[0]
        # Get the actual room_id from the cached data
        if selected_room_index >= len(self.available_rooms_cache):
             messagebox.showerror("Error", "Selected room index out of sync. Please find rooms again.")
             return
        selected_room_data = self.available_rooms_cache[selected_room_index]
        selected_room_id = selected_room_data['room_id']
        selected_room_number = selected_room_data['room_number']

        # 4. Get other details
        adults = self.adults_var.get()
        children = self.children_var.get()
        requests = self.requests_text.get("1.0", tk.END).strip() or None # Get text, strip whitespace, use None if empty

        # 5. Confirm and Add to DB
        guest_info = get_guest_by_id_db(self.selected_guest_id) # Get name for confirmation
        guest_name = f"{guest_info['first_name']} {guest_info['last_name']}" if guest_info else f"ID: {self.selected_guest_id}"

        confirm_msg = (
            f"Confirm Booking:\n\n"
            f"Guest: {guest_name}\n"
            f"Room: {selected_room_number}\n"
            f"Check-in: {check_in_date.isoformat()}\n"
            f"Check-out: {check_out_date.isoformat()}\n"
            f"Adults: {adults}, Children: {children}\n"
            f"Requests: {requests if requests else 'None'}\n"
        )
        if not messagebox.askyesno("Confirm Booking", confirm_msg):
            return # User cancelled

        self.controller.update_status("Creating reservation...")
        reservation_id = add_reservation_db(
            guest_id=self.selected_guest_id,
            room_id=selected_room_id,
            check_in=check_in_date.isoformat(),
            check_out=check_out_date.isoformat(),
            adults=adults,
            children=children,
            requests=requests
        )

        if reservation_id:
            messagebox.showinfo("Booking Confirmed", f"Reservation created successfully!\nBooking ID: {reservation_id}")
            self.controller.update_status(f"Reservation {reservation_id} created for room {selected_room_number}.")
            # Clear the form for next booking
            self.clear_form()
            # Optionally switch view
            # self.controller.show_frame("DashboardFrame")
        else:
            messagebox.showerror("Database Error", "Failed to create reservation in the database.")
            self.controller.update_status("Failed to create reservation.")


    def clear_form(self):
        """Resets the booking form fields."""
        self.guest_search_var.set("")
        self.guest_combobox['values'] = []
        self.guest_combobox.set("")
        self.selected_guest_id = None
        self.selected_guest_label.config(text="Selected Guest: None")

        self.checkin_entry.set_date(date.today())
        self.checkout_entry.set_date(date.today() + timedelta(days=1))
        self.update_checkout_mindate()

        self.rooms_listbox.delete(0, tk.END)
        self.available_rooms_cache.clear()

        self.adults_var.set(1)
        self.children_var.set(0)
        self.requests_text.delete("1.0", tk.END)

        self.controller.update_status("Booking form cleared.")