
import sqlite3
import pytest

from services.database_manager import DatabaseManager
from services.ecs_system import ECSSystem

@pytest.fixture
def ecs_system(tmp_path):
    db_path = tmp_path / "test_ecs.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE Employees (
            EmployeeID INTEGER PRIMARY KEY,
            FullName TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE Equipment (
            EquipmentID INTEGER PRIMARY KEY,
            EquipmentName TEXT NOT NULL,
            Status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE Transactions (
            TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmployeeID INTEGER,
            EquipmentID INTEGER,
            CheckoutTime TEXT,
            ReturnTime TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO Employees VALUES (?, ?)",
        (1001, "Test Employee")
    )

    cursor.execute(
        "INSERT INTO Equipment VALUES (?, ?, ?)",
        (1, "Hammer Drill", "Available")
    )

    conn.commit()
    conn.close()

    db_manager = DatabaseManager(str(db_path))
    return ECSSystem(db_manager)


def test_login_valid_employee(ecs_system):
    employee = ecs_system.login_employee(1001)

    assert employee is not None
    assert employee.employee_id == 1001
    assert employee.full_name == "Test Employee"


def test_checkout_equipment_changes_status(ecs_system):
    result = ecs_system.checkout_equipment(1001, 1)

    assert result is True

    available_equipment = ecs_system.get_available_equipment()

    assert len(available_equipment) == 0


def test_return_equipment_changes_status_to_available(ecs_system):
    ecs_system.checkout_equipment(1001, 1)

    result = ecs_system.return_equipment(1)

    assert result is True

    available_equipment = ecs_system.get_available_equipment()

    assert len(available_equipment) == 1
    assert available_equipment[0].equipment_id == 1
    assert available_equipment[0].status == "Available"