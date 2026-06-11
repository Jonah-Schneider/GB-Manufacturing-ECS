from models.employee import Employee
from models.equipment import Equipment
from models.transaction import Transaction
from services.database_manager import DatabaseManager


class ECSSystem:

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def login_employee(self, employee_id: int) -> Employee | None:
        """Look up an employee by ID.

        Args:
            employee_id (int): ID to look up.

        Returns:
            Employee | None  -> None when no matching employee row exists.
        """
        row = self.db_manager.get_employee(employee_id)
        if row is None:
            return None
        # row -> (EmployeeID, FullName)
        return Employee(row[0], row[1])

    def get_available_equipment(self) -> list[Equipment]:
        """List all equipment with status 'Available'.

        Returns:
            list[Equipment]
        """
        rows = self.db_manager.get_available_equipment()
        # row -> (EquipmentID, EquipmentName, Status)
        return [Equipment(row[0], row[1], row[2]) for row in rows]

    def checkout_equipment(self, employee_id: int, equipment_id: int) -> bool:
        """Check an item out: record a transaction + flag the item unavailable.

        Args:
            employee_id (int): employee performing the checkout.
            equipment_id (int): item being checked out.

        Returns:
            bool  -> True on success, False if the item is not currently
                     available (prevents a double checkout).
        """
        available_ids = [row[0] for row in self.db_manager.get_available_equipment()]
        if equipment_id not in available_ids:
            return False
        self.db_manager.create_transaction(employee_id, equipment_id)
        self.db_manager.update_equipment_status(equipment_id, "Checked Out")
        return True

    # used to view what equipment the individual employee has checked out.
    def get_employee_equipment(self, employee_id: int) -> list[Equipment]:
        """List the items one employee currently has checked out.

        Args:
            employee_id (int): employee whose open items to list.

        Returns:
            list[Equipment]
        """
        rows = self.db_manager.get_employee_equipment(employee_id)
        return [Equipment(row[0], row[1], row[2]) for row in rows]

    def return_equipment(self, equipment_id: int) -> bool:
        """Return an item: stamp the open transaction + flag it available.

        Args:
            equipment_id (int): item being returned.

        Returns:
            bool  -> True on success, False if the item had no open checkout.
        """
        updated = self.db_manager.close_transaction(equipment_id)
        if not updated:
            return False
        self.db_manager.update_equipment_status(equipment_id, "Available")
        return True

    def get_transactions(self) -> list[Transaction]:
        """List the full transaction log.

        Returns:
            list[Transaction]
        """
        rows = self.db_manager.get_transactions()
        # row -> (TransactionID, EmployeeID, EquipmentID, CheckoutTime, ReturnTime)
        return [Transaction(row[0], row[1], row[2], row[3], row[4]) for row in rows]
