#needed to connect with SQL 
import sqlite3
#for transaction times
import datetime

#Main class for the database_manager file. It connects to the already created SQL database and uses Sqlite to get and receive data from the table.
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
    #connect self to the self.db_path allows for the current instance to view the database and potentially edit it.
    def connect(self):
        return sqlite3.connect(self.db_path)

    
    #method to test that sqlite works and can connect to the database
    def test_connection(self):
        connection = self.connect()
        # .cursor creates a database object used to execute SQL commands and traverse the resulting data records, it is needed for Python to talk to SQL.
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM Equipment")
        #Grab everything from the created cursor and save it in the results object
        results = cursor.fetchall()

        print("Database Connected!")
        #prints every line of the data in cursor
        for row in results:
            print(row)
        #Closing the connection is essential to prevent memory leaks or inconsistent results when using other methods, it essentially says to SQL that it is done with this interaction.
        connection.close()

    #Connects to the database and grabs all equipment with a status of Available, it then closes the connection and returns the values. 
    def get_available_equipment(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Equipment WHERE Status = 'Available'")
        results = cursor.fetchall()
        conn.close()
        return results

    #Given an employee_ID it checks the employee table to see if it can find a match and returns the first one hence us using .fetchone with the cursor to ensure multiple results don't appear.
    def get_employee(self, employee_id):
        conn = self.connect()
        cursor = conn.cursor()
        #the statement "EmployeeID = ?" means that the value is not know when the method is created and the ID will be passed into the system to check by either the system or the user.
        cursor.execute("SELECT * FROM Employees WHERE EmployeeID = ?", (employee_id,))
        results = cursor.fetchone()
        conn.close()
        return results
    
    #Creates a new transaction and adds it to the transaction table given the equipment_id and the employee_id. It also collects the current time when the method was run to ensure more accurante time keeping of equipment.    
    def create_transaction(self, employee_id, equipment_id):
        conn = self.connect()
        cursor = conn.cursor()
        #datetime.datetime.now ensures we get the most present time, the format is then set up to show the current date as well as the current time in year, month, day and then hour, minute, second.
        checkout_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Transactions (EmployeeID, EquipmentID, CheckoutTime) VALUES (?, ?, ?)", (employee_id, equipment_id, checkout_time))
        #No return function because this is just changing the transaction database not returning a value to python also "?" is used for values that are not immeditately know AKA placeholders. Instead commit is used to update the transaction table.
        conn.commit()
        conn.close()

    #A simple method that can be used when an employee takes out equipment, it updates the status of an equipment into the status that is given in the method call. Again no data is being returned so commit is used instead of return.
    def update_equipment_status(self, equipment_id, status):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Equipment SET Status = ? WHERE EquipmentID = ?",
            (status, equipment_id)
        )
        conn.commit() 
        conn.close()
    
    #Returns all transactions so that the employee can view everything that has been taken out and returned and when it was taken out and returned. 
    def get_transactions(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Transactions")
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_employee_equipment(self, employee_id):
        conn = self.connect()
        cursor = conn.cursor()
        # Join Equipment and Transactions to find what the current employee has checked out
        #Executes a SQL query to select equipment details.
        #SELECT... pulls the EquipmentID, EquipmentName, and Status from the Equipment table.
        # JOIN Transactions ON links the Equipment table with a Transactions table to match equipment with user activity.
        # WHERE ... AND filters results to only show items that are currently assigned to the given employee_id AND have a status of 'Checked Out'.
        cursor.execute("""
            SELECT DISTINCT Equipment.EquipmentID, Equipment.EquipmentName, Equipment.Status
            FROM Equipment
            JOIN Transactions ON Equipment.EquipmentID = Transactions.EquipmentID
            WHERE Transactions.EmployeeID = ? AND Equipment.Status = 'Checked Out'
        """, (employee_id,))

        results = cursor.fetchall()
        conn.close()
        return results
    
    #Used to update the return time in a similar fashion to the checkout time being created in the create transaction method. 
    def record_return_time(self, equipment_id):
        conn = self.connect()
        cursor = conn.cursor()
        return_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE Transactions
            SET ReturnTime = ?
            WHERE EquipmentID = ? AND ReturnTime IS NULL
        """, (return_time, equipment_id))
        conn.commit()
        rows_updated = cursor.rowcount   # 0 if no open transaction was found
        conn.close()
        return rows_updated > 0          # True = success, False = nothing updated