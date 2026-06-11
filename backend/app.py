import os
from flask import Flask, request, jsonify, Response
from services.database_manager import DatabaseManager
from services.ecs_system import ECSSystem

app = Flask(__name__)

# Resolve the database path relative to this file (repo_root/database/ecs.db)
# so the app runs no matter what the current working directory is.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ecs.db")

db_manager = DatabaseManager(DB_PATH)
ecs = ECSSystem(db_manager)


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------
@app.route("/api/login/<int:employee_id>", methods=["GET"])
def login(employee_id: int) -> Response | tuple[Response, int]:
    """Look up an employee by ID.

    Args (URL):
        employee_id (int): numeric employee ID to look up.

    Calls:
        ecs.login_employee(employee_id)

    Returns:
        200 -> { "employee": { "employee_id": int, "full_name": str } }
        404 -> { "error": "employee not found" }
    """
    employee = ecs.login_employee(employee_id)
    if employee is None:
        return jsonify({"error": "employee not found"}), 404
    return jsonify({"employee": vars(employee)})


# -----------------------------------------------------------------------------
# EQUIPMENT — AVAILABILITY TRACKING
# -----------------------------------------------------------------------------
@app.route("/api/equipment", methods=["GET"])
def get_equipment() -> Response:
    """List equipment for the available-equipment panel (Core Feature: Availability).

    Args:
        none

    Calls:
        ecs.get_available_equipment()

    Returns:
        200 -> { "equipment": [ { "equipment_id": int,
                                  "equipment_name": str,
                                  "status": str }, ... ] }
    """
    items = ecs.get_available_equipment()
    return jsonify({"equipment": [vars(item) for item in items]})


# -----------------------------------------------------------------------------
# CHECKOUT
# -----------------------------------------------------------------------------
@app.route("/api/checkout", methods=["POST"])
def checkout() -> Response:
    """Check a piece of equipment out to an employee (Core Feature: Checkout).

    Args (JSON body):
        employee_id (int): employee performing the checkout.
        equipment_id (int): equipment item to check out.

    Calls:
        ecs.checkout_equipment(employee_id, equipment_id)

    Returns:
        200 -> { "success": true }
        200 -> { "success": false, "error": str }   # e.g. already checked out
    """
    data = request.get_json()
    employee_id = data["employee_id"]
    equipment_id = data["equipment_id"]
    if ecs.checkout_equipment(employee_id, equipment_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Equipment is not available"})


# -----------------------------------------------------------------------------
# RETURN
# -----------------------------------------------------------------------------
@app.route("/api/return", methods=["POST"])
def return_equipment() -> Response:
    """Return a checked-out equipment item (Core Feature: Return).

    Args (JSON body):
        equipment_id (int): equipment item being returned. The server resolves
                            the open checkout record for this item.

    Calls:
        ecs.return_equipment(equipment_id)

    Returns:
        200 -> { "success": true }
        200 -> { "success": false, "error": str }   # e.g. not checked out
    """
    data = request.get_json()
    equipment_id = data["equipment_id"]
    if ecs.return_equipment(equipment_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Item is not checked out"})


# -----------------------------------------------------------------------------
# EMPLOYEE — PERSONAL CHECKED-OUT LIST
# -----------------------------------------------------------------------------
@app.route("/api/employee/<int:employee_id>/equipment", methods=["GET"])
def get_employee_equipment(employee_id: int) -> Response:
    """List equipment currently checked out by one employee.

    Args (URL):
        employee_id (int): employee whose checked-out items to return.

    Calls:
        ecs.get_employee_equipment(employee_id)

    Returns:
        200 -> { "equipment": [ { "equipment_id": int,
                                  "equipment_name": str,
                                  "status": str }, ... ] }
    """
    items = ecs.get_employee_equipment(employee_id)
    return jsonify({"equipment": [vars(item) for item in items]})


# -----------------------------------------------------------------------------
# TRANSACTIONS
# -----------------------------------------------------------------------------
@app.route("/api/transactions", methods=["GET"])
def get_transactions() -> Response:
    """List the full transaction log (Core Feature: Viewing Transactions).

    Args:
        none

    Calls:
        ecs.get_transactions()

    Returns:
        200 -> { "transactions": [ { "transaction_id": int,
                                     "employee_id": int,
                                     "equipment_id": int,
                                     "checkout_time": str,
                                     "return_time": str | null }, ... ] }
    """
    items = ecs.get_transactions()
    return jsonify({"transactions": [vars(item) for item in items]})


if __name__ == "__main__":
    app.run(debug=True)
