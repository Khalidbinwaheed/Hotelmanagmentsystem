# gui/room_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
# Use relative import if running main.py from root
from ..db.room_queries import get_all_rooms_with_details, update_room_status_db
# Or use absolute if project root is in PYTHONPATH
# from db.room_queries import get_all_rooms_with_details, update_room_status_db

class RoomManagementFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.room_map = {} # Store room_id mapping for actions

        label = ttk.Label(self, text="Room Management", font=('Helvetica', 16, 'bold'))
        label.pack(pady=10)

        # --- Treeview for Room Data ---
        # Store original db column names for mapping if needed
        columns = ("room_no", "type", "status", "price", "floor")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        # Define headings
        self.tree.heading("room_no", text="Room No.")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")
        self.tree.heading("price", text="Price/Night ($)")
        self.tree.heading("floor", text="Floor")

        # Configure column widths
        self.tree.column("room_no", width=80, anchor=tk.CENTER)
        self.tree.column("type", width=120, anchor=tk.W)
        self.tree.column("status", width=100, anchor=tk.W)
        self.tree.column("price", width=100, anchor=tk.E)
        self.tree.column("floor", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        # --- Buttons for Room Actions ---
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        refresh_btn = ttk.Button(button_frame, text="Refresh List", command=self.refresh_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        clean_btn = ttk.Button(button_frame, text="Mark for Maintenance", command=self.mark_maintenance)
        clean_btn.pack(side=tk.LEFT, padx=5)

        available_btn = ttk.Button(button_frame, text="Mark as Available", command=self.mark_available)
        available_btn.pack(side=tk.LEFT, padx=5)

        # Populate the treeview initially
        self.refresh_data()

    def refresh_data(self):
        """Clears and reloads the room data from the database."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.room_map.clear() # Clear the room ID mapping

        # Load data from database
        rooms_list = get_all_rooms_with_details() # Call the DB function
        if rooms_list is None:
            messagebox.showerror("Database Error", "Could not fetch room data.")
            return

        for room in rooms_list:
            # Ensure all expected keys are present, handle potential None price
            price_display = f"{room.get('base_price', 0.0):.2f}" if room.get('base_price') is not None else "N/A"
            values = (
                room.get('room_number', 'N/A'),
                room.get('type_name', 'N/A'),
                room.get('status', 'Unknown'), # Use the status calculated in the query
                price_display,
                room.get('floor_number', 'N/A')
            )
            # Store the database room_id using the treeview item ID as the key
            item_id = self.tree.insert("", tk.END, values=values)
            self.room_map[item_id] = room.get('room_id') # Map tree item ID to DB room_id

        self.controller.update_status(f"Room list refreshed ({len(rooms_list)} rooms).")

    def get_selected_room_id(self):
        """Gets the database room_id of the currently selected item."""
        selected_item_id = self.tree.focus() # Get the Treeview item ID
        if not selected_item_id:
            messagebox.showwarning("No Selection", "Please select a room from the list first.")
            return None
        # Look up the database room_id using the map
        db_room_id = self.room_map.get(selected_item_id)
        if db_room_id is None:
             messagebox.showerror("Error", "Could not find database ID for selected room.")
             return None
        return db_room_id

    def mark_maintenance(self):
        """Marks the selected room for maintenance in the database."""
        room_id = self.get_selected_room_id()
        if room_id:
            # Check current status from DB if necessary (or rely on UI display)
            # For simplicity, assume we can always mark for maintenance unless occupied?
            # Let's just try the update. The query should handle checks if needed.
            if messagebox.askyesno("Confirm Maintenance", f"Mark room (ID: {room_id}) for maintenance?"):
                success = update_room_status_db(room_id=room_id, maintenance=True, availability=False) # Maintenance implies unavailable
                if success:
                    self.controller.update_status(f"Room {room_id} marked for maintenance.")
                    self.refresh_data() # Update the view
                else:
                    messagebox.showerror("Database Error", f"Failed to mark room {room_id} for maintenance.")

    def mark_available(self):
        """Marks the selected room as available in the database."""
        room_id = self.get_selected_room_id()
        if room_id:
             # Check current status? Maybe prevent marking occupied room as available directly.
            if messagebox.askyesno("Confirm Available", f"Mark room (ID: {room_id}) as available?"):
                # Reset maintenance and set availability to true
                success = update_room_status_db(room_id=room_id, availability=True, maintenance=False)
                if success:
                    self.controller.update_status(f"Room {room_id} marked as available.")
                    self.refresh_data() # Update the view
                else:
                    messagebox.showerror("Database Error", f"Failed to mark room {room_id} as available.")