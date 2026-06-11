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
 * Displays a welcome alert and immediately loads the employee's checked-out items
 * so the UI is populated right after login.
 */
async function loginEmployee() {
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
        // Send the login request to the backend.
        // GET /api/login/<id> looks up the employee record by numeric ID.
        const res = await fetch(`/api/login/${id}`);

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
    // This element must exist in the HTML with id="equipment-list".
    const container = document.getElementById('equipment-list');

    try {
        // Request the full list of equipment records from the server.
        const res = await fetch('/api/equipment');
        const data = await res.json();

        // Clear the container before rendering to prevent duplicate rows.
        // Pass null because we will append child elements ourselves below.
        setContainerContent(container, null);

        // Guard against an empty or malformed response body.
        if (!data || !data.equipment || data.equipment.length === 0) {
            // Show a user-facing message when the list is genuinely empty.
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
        // Log the error for debugging; show a user-facing error in the container
        // so the user knows the load failed rather than seeing stale or blank content.
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
        const res = await fetch('/api/checkout', {
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
            // The server responded but reported a business-logic failure
            // (e.g. item already checked out). Show its error message if present.
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
    try {
        // POST /api/return only needs the equipment ID — the server looks up
        // the current checkout record to mark it as returned.
        const res = await fetch('/api/return', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipment_id: equipmentId })
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
 *
 * NOTE: The #my-equipment-list container is expected to exist in the HTML.
 * It is created once at DOMContentLoaded (see bottom of file) so this function
 * never needs to create or inject the container itself — it only populates it.
 */
async function loadEmployeeEquipment() {
    // Do nothing if no employee is logged in — there is no ID to query against.
    if (!currentEmployeeId) return;

    // Locate the pre-existing container created during page initialisation.
    const container = document.getElementById('my-equipment-list');

    try {
        // Request only the equipment checked out by this specific employee.
        const res = await fetch(`/api/employee/${currentEmployeeId}/equipment`);
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
    // This allows the function to be called without crashing on pages that omit
    // the transaction panel.
    if (!container) return;

    try {
        // Fetch all transaction records from the server.
        const res = await fetch('/api/transactions');
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

            // Build the display string: transaction ID, employee, equipment, checkout time,
            // and optionally the return time if the item has been returned.
            const returnInfo = tx.return_time
                ? ` — returned ${tx.return_time}`  // Item has been returned
                : ' — not yet returned';            // Item is still checked out

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
// PAGE INITIALISATION
// ---------------------------------------------------------------------------

/**
 * DOMContentLoaded handler
 * Runs once the HTML document is fully parsed and all elements exist in the DOM.
 * Responsibilities:
 *   1. Ensure the #my-equipment-list container exists (creates it if absent).
 *   2. Wire all button click events using element IDs rather than positional
 *      querySelectorAll indices, so adding or reordering buttons in the HTML
 *      does not silently break the wiring.
 *
 * Expected HTML button IDs:
 *   - #login-btn              → triggers loginEmployee()
 *   - #view-equipment-btn     → triggers loadEquipment()
 *   - #view-my-equipment-btn  → triggers loadEmployeeEquipment()
 *   - #view-transactions-btn  → triggers loadTransactions()
 */
document.addEventListener('DOMContentLoaded', () => {

    // --- Ensure #my-equipment-list container exists ---
    // The employee equipment panel is populated dynamically after login.
    // Creating the container here (once, at startup) means loadEmployeeEquipment()
    // never has to check for or create it on every call.
    if (!document.getElementById('my-equipment-list')) {
        const myEquipmentContainer = document.createElement('div');
        myEquipmentContainer.id = 'my-equipment-list';
        // Append to the end of the body as a sensible default position.
        // Adjust this insertion point to match your actual HTML layout if needed.
        document.body.appendChild(myEquipmentContainer);
    }

    // --- Wire buttons by ID ---
    // Each button is looked up by its id attribute. If a button is missing from
    // the page (e.g. the transaction button on a page that doesn't show history),
    // the optional-chaining (?.) operator prevents a crash — it simply does nothing.

    // "Submit ID" / Login button
    document.getElementById('login-btn')
        ?.addEventListener('click', loginEmployee);

    // "View Equipment" button — loads the full available equipment list
    document.getElementById('view-equipment-btn')
        ?.addEventListener('click', loadEquipment);

    // "View My Items" button — loads equipment checked out by the logged-in employee
    document.getElementById('view-my-equipment-btn')
        ?.addEventListener('click', loadEmployeeEquipment);

    // "View Transactions" button — loads the full transaction history log
    document.getElementById('view-transactions-btn')
        ?.addEventListener('click', loadTransactions);
});