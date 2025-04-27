# gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox

# Import the frame classes using relative imports
from .dashboard_frame import DashboardFrame
from .room_frame import RoomManagementFrame
from .guest_frame import GuestManagementFrame
from .booking_frame import BookingFrame
from .checkinout_frame import CheckInOutFrame
# Add imports for other frames as you create them (e.g., services, payments)

class HotelApp(tk.Tk):
    """Main Application Window for the Hotel Management System."""

    def __init__(self):
        super().__init__()  # Initialize the tk.Tk parent class

        self.title("Hotel Management System - DB Connected")
        self.geometry("1000x700") # Increased size slightly

        # Configure root window grid to expand content
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Style ---
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam") # Try 'clam', 'alt', 'vista', etc.
        except tk.TclError:
            print("Selected theme not available, using default.")
            self.style.theme_use("default")

        # Configure styles for specific widgets
        self.style.configure("TLabel", padding=5, font=('Helvetica', 10))
        self.style.configure("TButton", padding=5, font=('Helvetica', 10))
        self.style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
        self.style.configure("TFrame", background='#f0f0f0')
        self.style.configure("TLabelframe.Label", font=('Helvetica', 12, 'bold')) # Style labelframe titles


        # --- Menu Bar ---
        self.create_menu()

        # --- Main Content Area ---
        self.container = ttk.Frame(self, padding="10 10 10 10")
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Dictionary to store frames (views)
        self.frames = {}

        # Create and store frames for each major section
        # Add other frames to this tuple as you create them
        for F in (DashboardFrame, RoomManagementFrame, GuestManagementFrame, BookingFrame, CheckInOutFrame):
            page_name = F.__name__
            # Pass the container as parent and self (HotelApp instance) as controller
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            # Place each frame in the same grid cell; only the top one will be visible
            frame.grid(row=0, column=0, sticky="nsew")

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Welcome to the Hotel Management System!")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.grid(row=2, column=0, sticky="ew") # Span across the bottom

        # Show the initial frame (Dashboard)
        self.show_frame("DashboardFrame")

    def create_menu(self):
        """Creates the main application menu bar."""
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        # --- File Menu ---
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        # Add options like Settings, Backup later?
        file_menu.add_command(label="Exit", command=self.quit)

        # --- View Menu ---
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", command=lambda: self.show_frame("DashboardFrame"))
        view_menu.add_separator()
        view_menu.add_command(label="Rooms", command=lambda: self.show_frame("RoomManagementFrame"))
        view_menu.add_command(label="Guests", command=lambda: self.show_frame("GuestManagementFrame"))
        # Add Reservations List view later?
        view_menu.add_separator()


        # --- Actions Menu ---
        actions_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Actions", menu=actions_menu)
        actions_menu.add_command(label="New Booking", command=lambda: self.show_frame("BookingFrame"))
        actions_menu.add_command(label="Check-in / Check-out", command=lambda: self.show_frame("CheckInOutFrame"))
        # Add Manage Services, Maintenance Request later?

        # --- Help Menu ---
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def show_frame(self, page_name):
        """Raises the requested frame to the top and refreshes its data if applicable."""
        if page_name not in self.frames:
            print(f"Error: Frame '{page_name}' not found.")
            return

        frame = self.frames[page_name]
        # Update status bar
        status_msg = page_name.replace('Frame', '') # Get a nicer name
        self.update_status(f"Viewing {status_msg}")
        frame.tkraise() # Bring the frame to the front

        # Refresh frame data if the frame has a 'refresh_data' method
        if hasattr(frame, 'refresh_data') and callable(getattr(frame, 'refresh_data')):
            try:
                frame.refresh_data()
            except Exception as e:
                messagebox.showerror("Refresh Error", f"Failed to refresh data for {status_msg}:\n{e}")
                print(f"Error refreshing {page_name}: {e}") # Log detailed error


    def show_about(self):
        """Displays a simple About dialog."""
        messagebox.showinfo("About", "Hotel Management System v1.1\nDatabase Connected\nCreated with Python and Tkinter")

    def update_status(self, message):
        """Updates the text in the status bar."""
        self.status_var.set(message)

    # You might add other controller methods here later, e.g.,
    # def get_current_user(self): -> To manage user logins
    # def confirm_action(self, title, message): -> Standard confirmation dialog