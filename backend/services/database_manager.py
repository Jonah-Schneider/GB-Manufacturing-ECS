#needed to connect with SQL 
import sqlite3
#for transaction times
import datetime

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
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Equipment WHERE Status = 'Available'")
        results = cursor.fetchall()
        conn.close()
        return results
     
    def get_employee(self, employee_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Employees WHERE EmployeeID = ?", (employee_id,))
        results = cursor.fetchone()
        conn.close()
        return results
    
    def create_transaction(self, employee_id, equipment_id):
        conn = self.connect()
        cursor = conn.cursor()
        checkout_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Transactions (EmployeeID, EquipmentID, CheckoutTime) VALUES (?, ?, ?)", (employee_id, equipment_id, checkout_time))
        #No return function because this is just changing the transaction database not returning a value to python also "?" is used for values that are not immeditately know AKA placeholders.
        conn.commit()
        conn.close()

    def update_equipment_status(self, equipment_id, status):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Equipment SET Status = ? WHERE EquipmentID = ?",
            (status, equipment_id)
        )
        conn.commit() 
        conn.close()
    
    def get_transactions(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Transactions")
        results = cursor.fetchall()
        conn.close()
        return results
    
    