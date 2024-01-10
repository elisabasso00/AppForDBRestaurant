import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

db_path="menu_database.db"

def create_table(cursor, table_name):
    # Create a table for each category
    query = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        price TEXT
    )
    '''
    cursor.execute(query)

def insert_data(cursor, table_name, item_name, price):
    # Insert data into the corresponding table if it doesn't already exist
    if not is_item_already_added(cursor, table_name, item_name):
        query = f'''
        INSERT INTO {table_name} (item_name, price) VALUES (?, ?)
        '''
        cursor.execute(query, (item_name, price))

def is_item_already_added(cursor, category, item_name):
    # Check if the item already exists in the category table
    query = f'''
    SELECT COUNT(*) FROM {category} WHERE item_name = ?
    '''
    cursor.execute(query, (item_name,))
    count = cursor.fetchone()[0]
    return count > 0

class MenuApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Menu Management")

        # Connect to the SQLite database
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        # Create a variable to store the selected user type
        self.user_type_var = tk.StringVar()

        # Ask for user type using a dropdown menu
        user_type_label = tk.Label(master, text="Select user type:")
        user_type_label.pack()

        user_type_menu = ttk.Combobox(master, textvariable=self.user_type_var, values=["Owner", "Customer"])
        user_type_menu.pack()

        confirm_button = tk.Button(master, text="Confirm", command=self.confirm_user_type)
        confirm_button.pack()

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        # Initialize self.notebook
        self.notebook = None

        # Initialize self.tables
        self.tables = {}



    def confirm_user_type(self):
        user_type = self.user_type_var.get().lower()  # Convert to lowercase for consistency

        if user_type not in ("owner", "customer"):
            messagebox.showerror("Error", "Invalid user type. Exiting.")
            self.master.destroy()
        else:
            # Store the selected user type
            self.user_type = user_type

            if self.user_type == "owner":
                # If the user is an owner, proceed with displaying the tables
                self.display_tables()
    
    def display_tables(self):
        # Initialize self.notebook
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill='both', expand=True)

        # Create tabs for each category
        for category in category_list:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=category)
            self.tables[category] = ttk.Treeview(frame, columns=('Item Name', 'Price'), show='headings')

            self.tables[category].heading('Item Name', text='Item Name')
            self.tables[category].heading('Price', text='Price')

            self.tables[category].pack(fill='both', expand=True)
            self.refresh_table(category)

        # Entry fields for new item
        self.item_name_entry = tk.Entry(self.master, width=20)
        self.item_name_entry.pack(side=tk.LEFT, padx=10)
        self.price_entry = tk.Entry(self.master, width=10)
        self.price_entry.pack(side=tk.LEFT, padx=10)

        # Add and Delete buttons
        self.add_button = tk.Button(self.master, text="Add Item", command=self.add_item)
        self.add_button.pack(side=tk.LEFT, padx=10)
        self.delete_button = tk.Button(self.master, text="Delete Item", command=self.delete_item)
        self.delete_button.pack(side=tk.LEFT, padx=10)

    def refresh_table(self, category):
        # Clear existing items in the table
        for item in self.tables[category].get_children():
            self.tables[category].delete(item)

        # Fetch data from the database and populate the table
        query = f"SELECT item_name, price FROM {category}"
        self.cursor.execute(query)
        data = self.cursor.fetchall()

        for row in data:
            self.tables[category].insert('', 'end', values=row)

    def add_item(self):
        category = self.notebook.tab(self.notebook.select(), "text")
        item_name = self.item_name_entry.get()
        price = self.price_entry.get()

        if item_name and price:
            # Check if the item has already been added
            if not is_item_already_added(self.cursor, category, item_name):
                try:
                    # Insert new item into the database
                    query = f"INSERT INTO {category} (item_name, price) VALUES (?, ?)"
                    self.cursor.execute(query, (item_name, price))

                    # Commit the changes
                    self.connection.commit()

                    # Refresh the table to display the updated data
                    self.refresh_table(category)

                    # Clear entry fields
                    self.item_name_entry.delete(0, tk.END)
                    self.price_entry.delete(0, tk.END)
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")
            else:
                messagebox.showwarning("Warning", "Item already exists in the database.")
        else:
            messagebox.showwarning("Warning", "Please enter both item name and price.")

    def delete_item(self):
        category = self.notebook.tab(self.notebook.select(), "text")
        selected_item = self.tables[category].selection()

        if selected_item:
            # Confirm deletion
            confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to delete this item?")
            if confirmation:
                # Delete selected item from the database
                item_name = self.tables[category].item(selected_item, "values")[0]
                try:
                    query = f"DELETE FROM {category} WHERE item_name = ?"
                    self.cursor.execute(query, (item_name,))
                    self.connection.commit()

                    # Refresh the table to display the updated data
                    self.refresh_table(category)
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Please select an item to delete.")

if __name__ == "__main__":
    # Specify the path to your text file
    file_path = 'menu.txt'

    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize category_list
    category_list = []

    # Connect to the SQLite database
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()


    current_category = None

    # Iterate through the lines in the file
    for line in lines:
        if line.startswith('#'):
            # If a new category starts, create a new table
            current_category = line.strip()[1:]  # Use the content after the hash as the category name
            create_table(cursor, current_category)
            category_list.append(current_category)
        else:
            # If not a category line, split the line into item name and price
            split_line = line.split('RM')

            if len(split_line) == 2:
                # If the line contains 'RM', unpack values
                item_name, price = map(str.strip, split_line)
                insert_data(cursor, current_category, item_name, f'RM{price}')

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    # Create Tkinter application
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()