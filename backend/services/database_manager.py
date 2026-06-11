import sqlite3
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

    def get_employee_equipment(self, employee_id: int) -> list[tuple]:
        """Return the equipment rows one employee currently has checked out.

        An item is "checked out by" an employee when a Transactions row links
        them and ReturnTime IS NULL. Join Transactions -> Equipment on that.

        Args:
            employee_id (int): employee whose open items to fetch.

        Returns:
            list[tuple]  -> Equipment rows (EquipmentID, EquipmentName, Status).
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Equipment.EquipmentID, Equipment.EquipmentName, Equipment.Status "
            "FROM Equipment "
            "JOIN Transactions ON Equipment.EquipmentID = Transactions.EquipmentID "
            "WHERE Transactions.EmployeeID = ? AND Transactions.ReturnTime IS NULL",
            (employee_id,)
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def close_transaction(self, equipment_id: int) -> int:
        """Stamp ReturnTime on the open transaction for an item (the "return").

        Find the Transactions row for this equipment_id where ReturnTime IS NULL
        and set ReturnTime to the current timestamp. Mirrors create_transaction,
        which sets CheckoutTime on insert.

        Args:
            equipment_id (int): item being returned.

        Returns:
            int  -> number of transaction rows updated (0 if the item was not
                    actually checked out).
        """
        conn = self.connect()
        cursor = conn.cursor()
        return_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE Transactions SET ReturnTime = ? "
            "WHERE EquipmentID = ? AND ReturnTime IS NULL",
            (return_time, equipment_id)
        )
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        return updated
