#needed to connect with SQL 
import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    
    #method to test that sqlite works and can connect to the database
    def test_connection(self):
        connection = self.connect()

        cursor = connection.cursor()

        cursor.execute("SELECT * FROM Equipment")

        results = cursor.fetchall()

        print("Database Connected!")

        for row in results:
            print(row)

        connection.close()

    def get_available_equipment(self):
        return
    def get_employee(self):
        return
    def create_transaction(self):
        return
    def update_equipment_status(self):
        return
    def get_transactions(self):
        return
    
    