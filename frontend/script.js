// script.js
// Frontend script that communicates with the backend REST API.
// Handles all UI interactions: employee login, viewing available equipment,
// checking out equipment, returning equipment, and viewing transaction history.
//
// ARCHITECTURE OVERVIEW:
// - All server communication is done via the Fetch API (async/await).
// - `currentEmployeeId` is the single piece of shared state — it tracks who is logged in.
// - Helper functions (`refreshLists`, `setContainerContent`) reduce repeated logic.
// - Button wiring uses element IDs instead of positional querySelectorAll to avoid
//   fragile index-based lookups that break if the HTML button order ever changes.
//
// NOTE ON BASE_URL:
// - Flask runs on port 5000. Live Server runs on port 5500.
// - Without BASE_URL, fetch() sends requests to Live Server (port 5500) instead
//   of Flask (port 5000), which causes all API calls to fail.
// - BASE_URL is defined once here so changing the port only requires one edit.

// ---------------------------------------------------------------------------
// BASE URL
// ---------------------------------------------------------------------------

// The address of the Flask backend server.
// All fetch() calls use this as a prefix so they reach Flask on port 5000
// instead of being intercepted by Live Server on port 5500.
const BASE_URL = 'http://127.0.0.1:5000';

// ---------------------------------------------------------------------------
// SHARED STATE
// ---------------------------------------------------------------------------

// Stores the numeric ID of the currently logged-in employee.
// Remains null until a successful login response is received from the server.
let currentEmployeeId = null;

// ---------------------------------------------------------------------------
// UTILITY / HELPER FUNCTIONS
// ---------------------------------------------------------------------------

/**
 * refreshLists
 * Convenience helper that reloads both the available-equipment list and the
 * logged-in employee's personal checked-out list in one call.
 * Called after any action (checkout or return) that changes equipment state,
 * so both panels stay in sync with the server without duplicating the two calls
 * in every function that needs them.
 */
function refreshLists() {
    loadEquipment();          // Reload the full available-equipment panel
    loadEmployeeEquipment();  // Reload the logged-in employee's checked-out panel
}

/**
 * setContainerContent
 * Small utility that safely writes content into a DOM container.
 * Clears whatever was previously rendered before writing new content,
 * preventing duplicate rows from accumulating on repeated loads.
 *
 * @param {HTMLElement} container - The DOM element to write into.
 * @param {string|null} message   - If provided, sets the element's text to this
 *                                  message (used for empty-state or error messages).
 *                                  Pass null when you intend to append child elements
 *                                  yourself after calling this function.
 */
function setContainerContent(container, message = null) {
    // Wipe any previously rendered rows or messages
    container.innerHTML = '';

    // If a plain-text message was provided (e.g. "No equipment available"),
    // write it directly and return early — no further DOM work needed.
    if (message !== null) {
        container.textContent = message;
    }
}

// ---------------------------------------------------------------------------
// AUTHENTICATION
// ---------------------------------------------------------------------------

/**
 * loginEmployee
 * Reads the employee ID from the login input field, calls GET /api/login/<id>,
 * and on success stores the returned employee ID in `currentEmployeeId`.
 * Saves the session to sessionStorage so the user stays logged in through
 * page interactions. Displays a welcome alert and immediately loads the
 * employee's checked-out items so the UI is populated right after login.
 */
async function loginEmployee() {
    //Check if someone is already logged in before logging them out
    if (currentEmployeeId) {
        const savedName = sessionStorage.getItem('employeeName');
        const confirm = window.confirm(
            `You are already logged in as ${savedName}. ` +
            `Do you want to log out and switch accounts?`
        );

        // If they click Cancel, stop here and keep the current session.
        if (!confirm) return;

        // If they click OK, log out the current user first before proceeding.
        logout();
    }
    
    
    
    // Grab the login input field — expected to have id="login-input" in the HTML
    const input = document.getElementById('login-input');

    // Parse the typed value as a base-10 integer.
    // parseInt returns NaN for non-numeric input, which isNaN() catches below.
    const id = parseInt(input.value, 10);

    // isNaN is used instead of `!id` to correctly reject 0 while still
    // accepting any valid positive integer employee ID.
    if (isNaN(id)) {
        alert('Please enter a valid employee ID');
        return; // Stop here — nothing to send to the server without a valid ID
    }

    try {
        // Send the login request to the Flask backend using the absolute BASE_URL.
        // GET /api/login/<id> looks up the employee record by numeric ID.
        const res = await fetch(`${BASE_URL}/api/login/${id}`);

        // A non-2xx HTTP status (e.g. 404 Not Found) means the ID wasn't found.
        if (!res.ok) {
            alert('Login failed — employee ID not found');
            return;
        }

        // Parse the JSON response body into a plain JavaScript object.
        const data = await res.json();

        // Confirm the response includes an employee object before proceeding.
        if (data && data.employee) {
            // Prefer the server-returned ID over the typed value in case the
            // backend normalises or reassigns IDs (e.g. trims leading zeros).
            currentEmployeeId = data.employee.employee_id || id;

            // Save the login to sessionStorage so it survives page interactions
            // without requiring the user to log in again after each action.
            sessionStorage.setItem('employeeId', currentEmployeeId);
            sessionStorage.setItem('employeeName', data.employee.full_name);

            // Show the logout button now that someone is logged in.
            document.getElementById('logout-btn').style.display = 'inline';

            // Greet the employee by name using the full_name field from the response.
            alert(`Welcome, ${data.employee.full_name || 'Employee'}!`);

            // Immediately populate the "My Equipment" panel so the employee can
            // see what they already have checked out without an extra click.
            loadEmployeeEquipment();
        }
    } catch (e) {
        // A thrown error here means a network-level failure (no response at all),
        // not a server error — log for debugging and inform the user.
        console.error('loginEmployee error:', e);
        alert('Network error — please try again');
    }
}

/**
 * logout
 * Clears the current session from both sessionStorage and the in-memory
 * state variable, resets the UI panels, and hides the logout button.
 * The user must log in again to perform any further actions.
 */
function logout() {
    // Clear the saved session data from sessionStorage
    sessionStorage.clear();

    // Reset the shared state variable so all action guards trigger correctly
    currentEmployeeId = null;

    // Clear the login input field so it is ready for the next user
    document.getElementById('login-input').value = '';

    // Hide the logout button — it will reappear on the next successful login
    document.getElementById('logout-btn').style.display = 'none';

    // Clear all panels so the next user does not see the previous user's data
    document.getElementById('equipment-list').innerHTML = '';
    document.getElementById('my-equipment-list').innerHTML = '';
    document.getElementById('transaction-list').innerHTML = '';

    alert('You have been logged out.');
}

// ---------------------------------------------------------------------------
// EQUIPMENT LIST (ALL AVAILABLE EQUIPMENT)
// ---------------------------------------------------------------------------

/**
 * loadEquipment
 * Fetches the full equipment catalogue from GET /api/equipment and renders
 * each item as a row inside the #equipment-list container.
 * Each row shows the equipment ID, name, and current status, plus a
 * "Checkout" button that calls checkoutEquipment() when clicked.
 */
async function loadEquipment() {
    // Target the container element where equipment rows will be rendered.
    const container = document.getElementById('equipment-list');

    try {
        // Request the full list of available equipment from the Flask backend.
        const res = await fetch(`${BASE_URL}/api/equipment`);
        const data = await res.json();

        // Clear the container before rendering to prevent duplicate rows.
        setContainerContent(container, null);

        // Guard against an empty or malformed response body.
        if (!data || !data.equipment || data.equipment.length === 0) {
            setContainerContent(container, 'No equipment available');
            return;
        }

        // Build one row per equipment item and append it to the container.
        data.equipment.forEach(eq => {
            // Create a <div> to hold this equipment item's text and button.
            const row = document.createElement('div');

            // Display the equipment's key details: ID, name, and availability status.
            row.textContent = `${eq.equipment_id} – ${eq.equipment_name} (${eq.status}) `;

            // Create a "Checkout" button for this item.
            const btn = document.createElement('button');
            btn.textContent = 'Checkout';

            // Wire the button so clicking it passes this item's ID to checkoutEquipment.
            // The arrow function captures `eq.equipment_id` from the current loop iteration.
            btn.onclick = () => checkoutEquipment(eq.equipment_id);

            // Attach the button to the row, then attach the row to the container.
            row.appendChild(btn);
            container.appendChild(row);
        });
    } catch (e) {
        console.error('loadEquipment error:', e);
        setContainerContent(container, 'Error loading equipment — please try again');
    }
}

// ---------------------------------------------------------------------------
// CHECKOUT
// ---------------------------------------------------------------------------

/**
 * checkoutEquipment
 * Sends a checkout request to POST /api/checkout for the currently logged-in
 * employee and the specified equipment item.
 * On success, both equipment lists are refreshed so the UI reflects the new state.
 *
 * @param {number} equipmentId - The numeric ID of the equipment item to check out.
 */
async function checkoutEquipment(equipmentId) {
    // Prevent checkout attempts before login — the server would reject them anyway,
    // but catching it here gives the user a clearer, faster error message.
    if (!currentEmployeeId) {
        alert('Please log in before checking out equipment');
        return;
    }

    try {
        // POST /api/checkout expects a JSON body with both IDs.
        const res = await fetch(`${BASE_URL}/api/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Serialise the request payload to JSON for the server to parse.
            body: JSON.stringify({
                employee_id: currentEmployeeId,
                equipment_id: equipmentId
            })
        });

        // Parse the server's response to check whether the checkout succeeded.
        const data = await res.json();

        if (data.success) {
            alert('Equipment checked out successfully');
            // Refresh both lists so the checked-out item disappears from the
            // available list and appears in the employee's personal list.
            refreshLists();
        } else {
            // The server responded but reported a business-logic failure.
            alert(data.error || 'Checkout failed — please try again');
        }
    } catch (e) {
        console.error('checkoutEquipment error:', e);
        alert('Network error — please try again');
    }
}

// ---------------------------------------------------------------------------
// RETURN
// ---------------------------------------------------------------------------

/**
 * returnEquipment
 * Sends a return request to POST /api/return for a specific equipment item.
 * On success, refreshes both equipment lists so the UI matches server state.
 *
 * @param {number} equipmentId - The numeric ID of the equipment item being returned.
 */
async function returnEquipment(equipmentId) {
    // Prevent return attempts before login — the server would reject them anyway,
    // but catching it here gives the user a clearer, faster error message.
    if (!currentEmployeeId) {
        alert('Please log in before returning equipment');
        return;
    }

    try {
        // POST /api/return only needs the equipment ID — the server looks up
        // the current checkout record to mark it as returned.
        const res = await fetch(`${BASE_URL}/api/return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                employee_id: currentEmployeeId,
                equipment_id: equipmentId
            })
        });

        // Parse the server's response to determine success or failure.
        const data = await res.json();

        if (data.success) {
            alert('Equipment returned successfully');
            // Refresh both lists: the item should reappear as available and
            // disappear from the employee's personal checked-out list.
            refreshLists();
        } else {
            alert(data.error || 'Return failed — please try again');
        }
    } catch (e) {
        console.error('returnEquipment error:', e);
        alert('Network error — please try again');
    }
}

// ---------------------------------------------------------------------------
// EMPLOYEE EQUIPMENT (PERSONAL CHECKED-OUT LIST)
// ---------------------------------------------------------------------------

/**
 * loadEmployeeEquipment
 * Fetches the list of equipment currently checked out by the logged-in employee
 * from GET /api/employee/<id>/equipment and renders it into #my-equipment-list.
 * Each row shows item details and a "Return" button that calls returnEquipment().
 */
async function loadEmployeeEquipment() {
    // Do nothing if no employee is logged in — there is no ID to query against.
    if (!currentEmployeeId) return;

    // Locate the container for this employee's checked-out items.
    const container = document.getElementById('my-equipment-list');

    try {
        // Request only the equipment checked out by this specific employee.
        const res = await fetch(`${BASE_URL}/api/employee/${currentEmployeeId}/equipment`);
        const data = await res.json();

        // Clear the container before rendering the fresh data.
        setContainerContent(container, null);

        // Show a friendly empty-state message if the employee has nothing checked out.
        if (!data || !data.equipment || data.equipment.length === 0) {
            setContainerContent(container, 'No items currently checked out');
            return;
        }

        // Render one row per checked-out item.
        data.equipment.forEach(eq => {
            const row = document.createElement('div');

            // Display the equipment's ID, name, and current status.
            row.textContent = `${eq.equipment_id} – ${eq.equipment_name} (${eq.status}) `;

            // Create a "Return" button so the employee can return the item inline.
            const btn = document.createElement('button');
            btn.textContent = 'Return';

            // Wire the button to pass this item's ID to returnEquipment on click.
            btn.onclick = () => returnEquipment(eq.equipment_id);

            row.appendChild(btn);
            container.appendChild(row);
        });
    } catch (e) {
        console.error('loadEmployeeEquipment error:', e);
        setContainerContent(container, 'Error loading your equipment — please try again');
    }
}

// ---------------------------------------------------------------------------
// TRANSACTION HISTORY
// ---------------------------------------------------------------------------

/**
 * loadTransactions
 * Fetches the full transaction log from GET /api/transactions and renders each
 * record into the #transaction-list container.
 * This is a read-only view — no actions can be taken from this panel.
 */
async function loadTransactions() {
    const container = document.getElementById('transaction-list');

    // If the container doesn't exist in the current page layout, exit silently.
    if (!container) return;

    try {
        // Fetch all transaction records from the Flask backend.
        const res = await fetch(`${BASE_URL}/api/transactions`);
        const data = await res.json();

        // Clear any previously rendered rows before writing new content.
        setContainerContent(container, null);

        // Show an empty-state message when no transactions exist yet.
        if (!data || !data.transactions || data.transactions.length === 0) {
            setContainerContent(container, 'No transactions on record');
            return;
        }

        // Render one row per transaction record.
        data.transactions.forEach(tx => {
            const row = document.createElement('div');

            // Build the display string. return_time will be null if the item
            // has not been returned yet, so we show a friendly message instead.
            const returnInfo = tx.return_time
                ? ` — returned ${tx.return_time}`
                : ' — not yet returned';

            row.textContent =
                `#${tx.transaction_id}: ` +
                `Employee ${tx.employee_id} | ` +
                `Equipment ${tx.equipment_id} | ` +
                `Checked out: ${tx.checkout_time}` +
                returnInfo;

            container.appendChild(row);
        });
    } catch (e) {
        console.error('loadTransactions error:', e);
        setContainerContent(container, 'Error loading transactions — please try again');
    }
}

// ---------------------------------------------------------------------------
// PAGE INITIALISATION — single DOMContentLoaded block
// ---------------------------------------------------------------------------

/**
 * DOMContentLoaded handler
 * Runs once when the page finishes loading. Handles two jobs in one place:
 * 1. Restores a previous session from sessionStorage if one exists, so the
 *    user stays logged in through page interactions without re-entering their ID.
 * 2. Wires all button click events so user interactions call the right functions.
 * Keeping both jobs in a single block prevents buttons from being wired twice,
 * which was causing the welcome back alert to fire on every action.
 */
document.addEventListener('DOMContentLoaded', () => {

    // Ensure the #my-equipment-list container exists. It is declared in the HTML
    // but this acts as a safety net in case it is ever accidentally removed.
    if (!document.getElementById('my-equipment-list')) {
        const myEquipmentContainer = document.createElement('div');
        myEquipmentContainer.id = 'my-equipment-list';
        document.body.appendChild(myEquipmentContainer);
    }

    // ── SESSION RESTORE ──────────────────────────────────────────────────────
    // Check sessionStorage for a previously saved login. If found, restore the
    // session silently — no alert, just populate the state and show the logout
    // button so the user can see they are still logged in.
    const savedId = sessionStorage.getItem('employeeId');
    const savedName = sessionStorage.getItem('employeeName');

    if (savedId) {
        // Restore the in-memory state variable from the saved session.
        currentEmployeeId = parseInt(savedId, 10);

        // Fill the login input so the user can see which ID is active.
        document.getElementById('login-input').value = savedId;

        // Show the logout button — the user is already logged in.
        document.getElementById('logout-btn').style.display = 'inline';

        // Load the employee's checked-out items silently with no alert,
        // so the UI is populated without interrupting the user.
        loadEmployeeEquipment();
    }

    // ── BUTTON WIRING ────────────────────────────────────────────────────────
    // Wire each button exactly once using its element ID.
    // The optional-chaining operator (?.) prevents a crash if a button is
    // ever accidentally removed from the HTML.
    document.getElementById('login-btn')
        ?.addEventListener('click', loginEmployee);

    document.getElementById('logout-btn')
        ?.addEventListener('click', logout);

    document.getElementById('view-equipment-btn')
        ?.addEventListener('click', loadEquipment);

    document.getElementById('view-my-equipment-btn')
        ?.addEventListener('click', loadEmployeeEquipment);

    document.getElementById('view-transactions-btn')
        ?.addEventListener('click', loadTransactions);
});