#Need to import models to use as objects for the project otherwise they don't exist to the code.
from models.employee import Employee
from models.equipment import Equipment
from models.transaction import Transaction

class ECSSystem:
    def __init__(self, db_manager):
        # Store the database manager for all data access
        self.db_manager = db_manager

    def login_employee(self, employee_id):
        # Look up an employee by ID
        row = self.db_manager.get_employee(employee_id)  # Fixed: was get_employee_by_id

        if row is None:
            return None

        # Convert the database row into an Employee object
        return Employee(*row)

    def get_available_equipment(self):
        # Get all equipment with status Available
        rows = self.db_manager.get_available_equipment()

        # Convert each row into an Equipment object
        return [Equipment(*row) for row in rows]

    def checkout_equipment(self, employee_id, equipment_id):
        # Create a transaction record for the checkout
        self.db_manager.create_transaction(employee_id, equipment_id)

        # Update the equipment status to Checked Out
        self.db_manager.update_equipment_status(equipment_id, "Checked Out")

    # Used to view what equipment the individual employee has checked out
    def get_employee_equipment(self, employee_id):
        # Get all equipment checked out by this employee
        rows = self.db_manager.get_employee_equipment(employee_id) #Created new method just for this that gets only the equipment taken out by the current employee

        # Convert each row into an Equipment object
        return [Equipment(*row) for row in rows]

    def return_equipment(self, equipment_id):
        # Update the equipment status back to Available
        self.db_manager.update_equipment_status(equipment_id, "Available")

        # Record the return time for the open transaction
        self.db_manager.record_return_time(equipment_id)  # Fixed: was return_equipment

    def get_transactions(self):
        # Get the full transaction history
        rows = self.db_manager.get_transactions()

        # Convert each row into a Transaction object
        return [Transaction(*row) for row in rows]