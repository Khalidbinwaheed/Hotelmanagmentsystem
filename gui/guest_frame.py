# gui/guest_frame.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
# Use relative imports for DB functions
from ..db.guest_queries import get_all_guests, add_guest_db, find_guest_by_name_db
# Import update/delete later: from ..db.guest_queries import update_guest_db, delete_guest_db

class GuestManagementFrame(ttk.Frame):
    """Frame for viewing and managing hotel guests."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.guest_map = {} # Map treeview item ID to guest_id

        label = ttk.Label(self, text="Guest Management", font=('Helvetica', 16, 'bold'))
        label.pack(pady=(10,5))

        # --- Search Bar ---
        search_frame = ttk.Frame(self, padding=(0, 5))
        search_frame.pack(fill=tk.X, padx=10)
        ttk.Label(search_frame, text="Search Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_guests)
        search_btn.pack(side=tk.LEFT, padx=5)
        clear_btn = ttk.Button(search_frame, text="Clear", command=self.clear_search)
        clear_btn.pack(side=tk.LEFT)


        # --- Treeview for Guest Data ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        columns = ("guest_id", "first_name", "last_name", "email", "phone")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("guest_id", text="ID")
        self.tree.heading("first_name", text="First Name")
        self.tree.heading("last_name", text="Last Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("phone", text="Phone")

        self.tree.column("guest_id", width=50, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column("first_name", width=150, anchor=tk.W)
        self.tree.column("last_name", width=150, anchor=tk.W)
        self.tree.column("email", width=200, anchor=tk.W)
        self.tree.column("phone", width=120, anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Buttons for Guest Actions ---
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        refresh_btn = ttk.Button(button_frame, text="Refresh List", command=self.refresh_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        add_btn = ttk.Button(button_frame, text="Add New Guest", command=self.add_guest)
        add_btn.pack(side=tk.LEFT, padx=5)

        # Add Edit/Delete later
        # edit_btn = ttk.Button(button_frame, text="Edit Selected", command=self.edit_guest)
        # edit_btn.pack(side=tk.LEFT, padx=5)
        # delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self.delete_guest)
        # delete_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_data() # Load initial data

    def _populate_tree(self, guests_list):
        """Helper to populate treeview, clearing first."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.guest_map.clear()

        if guests_list is None:
            messagebox.showerror("Database Error", "Could not fetch guest data.")
            return

        for guest in guests_list:
            values = (
                guest.get('guest_id', 'N/A'),
                guest.get('first_name', ''),
                guest.get('last_name', ''),
                guest.get('email', ''),
                guest.get('phone', '')
            )
            item_id = self.tree.insert("", tk.END, values=values)
            self.guest_map[item_id] = guest.get('guest_id') # Map tree item ID to DB guest_id

    def refresh_data(self):
        """Clears search and reloads all guest data from the database."""
        self.search_var.set("") # Clear search field
        self.controller.update_status("Fetching all guests...")
        guests = get_all_guests()
        self._populate_tree(guests)
        self.controller.update_status(f"Guest list refreshed ({len(guests or [])} guests).")

    def search_guests(self):
        """Filters the guest list based on the search term."""
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showwarning("Search", "Please enter a name to search for.")
            return
        self.controller.update_status(f"Searching guests for '{search_term}'...")
        guests = find_guest_by_name_db(search_term)
        self._populate_tree(guests)
        self.controller.update_status(f"Found {len(guests or [])} guests matching '{search_term}'.")

    def clear_search(self):
        """Clears the search results and shows all guests."""
        self.refresh_data()


    def add_guest(self):
        """Opens dialogs to add a new guest and saves to DB."""
        fname = simpledialog.askstring("New Guest", "Enter First Name:", parent=self)
        if not fname: return
        lname = simpledialog.askstring("New Guest", "Enter Last Name:", parent=self)
        if not lname: return
        email = simpledialog.askstring("New Guest", f"Enter Email for {fname} {lname}:", parent=self)
        # Basic email validation could be added here
        phone = simpledialog.askstring("New Guest", f"Enter Phone for {fname} {lname}:", parent=self)
        if not phone:
             messagebox.showwarning("Input Required", "Phone number is required.")
             return

        # Optional fields
        address = simpledialog.askstring("New Guest (Optional)", "Enter Address:", parent=self)
        city = simpledialog.askstring("New Guest (Optional)", "Enter City:", parent=self)
        country = simpledialog.askstring("New Guest (Optional)", "Enter Country:", parent=self)

        # Add more dialogs for passport, DOB if needed

        self.controller.update_status(f"Adding guest {fname} {lname}...")
        guest_id = add_guest_db(
            first_name=fname.strip(),
            last_name=lname.strip(),
            email=email.strip() if email else None, # Handle empty optional email
            phone=phone.strip(),
            address=address.strip() if address else None,
            city=city.strip() if city else None,
            country=country.strip() if country else None
        )

        if guest_id:
            messagebox.showinfo("Guest Added", f"Guest '{fname} {lname}' added successfully (ID: {guest_id}).")
            self.controller.update_status(f"Guest {fname} {lname} added.")
            self.refresh_data() # Update the view
        else:
            messagebox.showerror("Database Error", "Failed to add guest to the database.")
            self.controller.update_status("Failed to add guest.")

    def get_selected_guest_id(self):
         """Gets the database guest_id of the currently selected item."""
         selected_item_id = self.tree.focus()
         if not selected_item_id:
             messagebox.showwarning("No Selection", "Please select a guest from the list first.")
             return None
         db_guest_id = self.guest_map.get(selected_item_id)
         if db_guest_id is None:
              messagebox.showerror("Error", "Could not find database ID for selected guest.")
              return None
         return db_guest_id

    # --- Placeholder functions for Edit/Delete ---
    # def edit_guest(self):
    #     guest_id = self.get_selected_guest_id()
    #     if guest_id:
    #         # 1. Fetch full guest data using get_guest_by_id_db(guest_id)
    #         # 2. Open a new Toplevel window or dialog pre-filled with data
    #         # 3. Allow user to edit fields
    #         # 4. On save, call update_guest_db(...) function (needs to be created in db/guest_queries.py)
    #         # 5. Refresh list
    #         messagebox.showinfo("Not Implemented", f"Editing guest ID {guest_id} is not yet implemented.")

    # def delete_guest(self):
    #     guest_id = self.get_selected_guest_id()
    #     if guest_id:
    #          # IMPORTANT: Check for existing reservations before deleting!
    #          # This requires a new DB query function, e.g., check_guest_reservations(guest_id)
    #          can_delete = False # Replace with result of check_guest_reservations
    #          if not can_delete:
    #               messagebox.showerror("Deletion Blocked", f"Cannot delete guest ID {guest_id}. They have existing reservations.")
    #               return

    #          if messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete guest ID {guest_id}?"):
    #               # Call delete_guest_db(guest_id) function (needs creation)
    #               # Refresh list
    #               messagebox.showinfo("Not Implemented", f"Deleting guest ID {guest_id} is not yet implemented.")