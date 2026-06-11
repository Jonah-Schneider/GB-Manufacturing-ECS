
# This is the Flask web server entry point. It creates the app, connects to the database, and defines all API routes that the frontend (script.js) can call.
# Each route receives a request from the browser, calls the appropriate ECSSystem method, and sends back a JSON response.

# flask_cors allows the browser to make fetch() calls to Flask from an HTML file.
# Without this, the browser blocks all requests due to CORS (Cross-Origin Resource Sharing) policy.
from flask_cors import CORS

# os is used to build the database file path dynamically so the app works regardless of what folder it is launched from.
import os

# Flask: the web framework that handles routing and running the server.
# request: used to read incoming JSON data from POST requests.
# jsonify: converts Python dictionaries into proper JSON responses.
# Response: used as a type hint so the code is easier to read and understand.
from flask import Flask, request, jsonify, Response

# Import the DatabaseManager class which handles all direct SQLite communication.
from services.database_manager import DatabaseManager

# Import the ECSSystem class which contains all business logic (login, checkout, return, etc.)
from services.ecs_system import ECSSystem

# Create the Flask application instance. __name__ tells Flask where to look for files and resources relative to this file's location.
app = Flask(__name__)

# Apply CORS to the entire app — this tells the browser it is allowed to send
# fetch() requests to this server from any origin (including a local HTML file).
CORS(app)

# -----------------------------------------------------------------------------
# DATABASE SETUP
# -----------------------------------------------------------------------------

# Build the absolute path to the database file so it works no matter where
# the app is launched from. 
# os.path.abspath(__file__) gets the full path to this file (app.py).
# os.path.dirname() moves up one folder level.
# Calling dirname() twice moves up to the project root (GB-Manufacturing-ECS/).
# os.path.join() then adds "database/ecs.db" to reach the database file.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ecs.db")

# Create a single DatabaseManager instance using the resolved path.
# This object is shared by all routes through the ECSSystem instance below.
db_manager = DatabaseManager(DB_PATH)

# Create a single ECSSystem instance, passing in the DatabaseManager.
# All routes call methods on this object rather than touching the database directly.
ecs = ECSSystem(db_manager)


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------

# @app.route defines a URL path and the HTTP method the route responds to.
# "GET" is used here because we are only retrieving data, not changing anything.
# <int:employee_id> is a URL parameter — Flask extracts the integer from the URL
# and passes it directly into the function as the employee_id argument.
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
    # Ask ECSSystem to look up the employee. Returns an Employee object or None.
    employee = ecs.login_employee(employee_id)

    # If no employee was found, return a 404 (Not Found) response with an error message.
    # The frontend checks for this and shows "Login failed" to the user.
    if employee is None:
        return jsonify({"error": "employee not found"}), 404

    # vars() converts the Employee object's attributes into a plain dictionary
    # so jsonify can turn it into JSON. Example: {"employee_id": 1001, "full_name": "Jonah Schneider"}
    return jsonify({"employee": vars(employee)})


# -----------------------------------------------------------------------------
# EQUIPMENT — AVAILABILITY TRACKING
# -----------------------------------------------------------------------------

@app.route("/api/equipment", methods=["GET"])
def get_equipment() -> Response:
    """List all currently available equipment.

    Args:
        none

    Calls:
        ecs.get_available_equipment()

    Returns:
        200 -> { "equipment": [ { "equipment_id": int,
                                  "equipment_name": str,
                                  "status": str }, ... ] }
    """
    # Ask ECSSystem for all equipment with status "Available".
    # Returns a list of Equipment objects.
    items = ecs.get_available_equipment()

    # Convert each Equipment object into a dictionary using vars(), then wrap
    # the list in a JSON response. The frontend loops over this list to build
    # the equipment rows with Checkout buttons.
    return jsonify({"equipment": [vars(item) for item in items]})


# -----------------------------------------------------------------------------
# CHECKOUT
# -----------------------------------------------------------------------------

# "POST" is used here because this route changes data — it creates a transaction
# and updates equipment status. The employee and equipment IDs are sent in the
# request body as JSON rather than in the URL.
@app.route("/api/checkout", methods=["POST"])
def checkout() -> Response:
    """Check a piece of equipment out to an employee.

    Args (JSON body):
        employee_id (int): employee performing the checkout.
        equipment_id (int): equipment item to check out.

    Calls:
        ecs.checkout_equipment(employee_id, equipment_id)

    Returns:
        200 -> { "success": true }
        400 -> { "success": false, "error": "Missing required fields" }
        200 -> { "success": false, "error": "Equipment is not available" }
    """
    # request.get_json() reads and parses the JSON body sent by the frontend.
    # Returns a Python dictionary, or None if the body is missing or not valid JSON.
    data = request.get_json()

    # Validate the request before doing anything with it.
    # If the body is missing or either required field is absent, return a 400
    # (Bad Request) response immediately. This prevents a crash from trying
    # to access a key that doesn't exist in the dictionary.
    if not data or "employee_id" not in data or "equipment_id" not in data:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # Extract the two IDs from the validated request body.
    employee_id = data["employee_id"]
    equipment_id = data["equipment_id"]

    # Ask ECSSystem to perform the checkout. Returns True on success, False if
    # the equipment is unavailable.
    if ecs.checkout_equipment(employee_id, equipment_id):
        return jsonify({"success": True})

    # If checkout_equipment returned False, let the frontend know why it failed.
    return jsonify({"success": False, "error": "Equipment is not available"})


# -----------------------------------------------------------------------------
# RETURN
# -----------------------------------------------------------------------------

@app.route("/api/return", methods=["POST"])
def return_equipment() -> Response:
    """Return a checked-out equipment item.

    Args (JSON body):
        equipment_id (int): equipment item being returned. The server resolves
                            the open checkout record for this item automatically.

    Calls:
        ecs.return_equipment(equipment_id)

    Returns:
        200 -> { "success": true }
        400 -> { "success": false, "error": "Missing required fields" }
        200 -> { "success": false, "error": "Item is not checked out" }
    """
    # Read and parse the JSON body from the frontend request.
    data = request.get_json()

    # Validate that the body exists and contains the required equipment_id field.
    # Without this guard, a missing field would crash Flask with a KeyError.
    if not data or "equipment_id" not in data:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # Extract the equipment ID from the validated request body.
    equipment_id = data["equipment_id"]

    # Ask ECSSystem to process the return. Returns True on success, False if
    # the item was not currently checked out.
    if ecs.return_equipment(equipment_id):
        return jsonify({"success": True})

    # If return_equipment returned False, inform the frontend of the failure.
    return jsonify({"success": False, "error": "Item is not checked out"})


# -----------------------------------------------------------------------------
# EMPLOYEE — PERSONAL CHECKED-OUT LIST
# -----------------------------------------------------------------------------

@app.route("/api/employee/<int:employee_id>/equipment", methods=["GET"])
def get_employee_equipment(employee_id: int) -> Response:
    """List equipment currently checked out by one specific employee.

    Args (URL):
        employee_id (int): employee whose checked-out items to return.

    Calls:
        ecs.get_employee_equipment(employee_id)

    Returns:
        200 -> { "equipment": [ { "equipment_id": int,
                                  "equipment_name": str,
                                  "status": str }, ... ] }
    """
    # Ask ECSSystem for all equipment currently checked out by this employee.
    # Returns a list of Equipment objects (may be empty if nothing is checked out).
    items = ecs.get_employee_equipment(employee_id)

    # Convert each Equipment object to a dictionary and wrap in a JSON response.
    # The frontend uses this list to build the "My Equipment" panel with Return buttons.
    return jsonify({"equipment": [vars(item) for item in items]})


# -----------------------------------------------------------------------------
# TRANSACTIONS
# -----------------------------------------------------------------------------

@app.route("/api/transactions", methods=["GET"])
def get_transactions() -> Response:
    """List the full transaction log — every checkout and return event ever recorded.

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
    # Ask ECSSystem for all transaction records from the database.
    # Returns a list of Transaction objects.
    items = ecs.get_transactions()

    # Convert each Transaction object to a dictionary and wrap in a JSON response.
    # return_time will be None for items still checked out, which jsonify
    # automatically converts to null in the JSON output.
    return jsonify({"transactions": [vars(item) for item in items]})


# -----------------------------------------------------------------------------
# SERVER STARTUP
# -----------------------------------------------------------------------------

# This block only runs when you execute app.py directly (python app.py).
# It will not run if the file is imported by another module.
# debug=True enables automatic reloading when you save changes to the file
# and shows detailed error messages in the browser during development.
if __name__ == "__main__":
    app.run(debug=True)