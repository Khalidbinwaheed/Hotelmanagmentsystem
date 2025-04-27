# db/connection.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG # Import config from the root level

def get_db_connection():
    """ Establishes a connection to the MySQL database. """
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG) # Unpack config dict
        # print("MySQL Database connection successful") # Optional: for debugging
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        # In a real app, you might want to raise the error or handle it differently
    return connection

# Example of using a connection (can be used within query files)
# def execute_query(query, params=None, fetch=False):
#     """ Utility to execute a query - might be useful later """
#     conn = get_db_connection()
#     if conn is None:
#         return None # Or raise an exception

#     cursor = conn.cursor(dictionary=True) # dictionary=True returns results as dicts
#     result = None
#     try:
#         cursor.execute(query, params or ())
#         if fetch:
#             result = cursor.fetchall() # Or fetchone() if needed
#         else:
#             conn.commit() # Commit changes for INSERT, UPDATE, DELETE
#             result = cursor.lastrowid # Useful for INSERTs
#     except Error as e:
#         print(f"Error executing query: {e}")
#         conn.rollback() # Rollback on error
#     finally:
#         cursor.close()
#         conn.close()
#     return result

# Note: Constantly opening/closing connections can be inefficient.
# For larger apps, consider connection pooling.
# For this example, we'll mostly get connection/cursor within each query function.