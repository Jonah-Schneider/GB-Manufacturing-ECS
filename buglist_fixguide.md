# ECS Project — Bug List & Fix Guide

**Project:** GB Manufacturing Equipment Checkout System  
**Files affected:** `ecs_system.py`, `database_manager.py`, `script.js`, `style.css`

---

## Bug 1 — Equipment can be checked out twice

**Symptom:** Clicking Checkout on an item that is already checked out creates a second
transaction. The item then appears twice in "My Equipment."

**Root cause:** `checkout_equipment()` in `ecs_system.py` inserts a transaction and
updates the equipment status unconditionally — it never checks whether the item is
already checked out before proceeding.

**Fix — `ecs_system.py`**

Replace the existing `checkout_equipment` method:

```python
def checkout_equipment(self, employee_id, equipment_id):
    # Guard: verify the item is actually available before allowing checkout.
    # get_available_equipment() returns only rows with Status = 'Available'.
    rows = self.db_manager.get_available_equipment()
    available_ids = [row[0] for row in rows]   # row[0] is EquipmentID
    if equipment_id not in available_ids:
        return False   # Flask route sends {"success": false} to the frontend

    self.db_manager.create_transaction(employee_id, equipment_id)
    self.db_manager.update_equipment_status(equipment_id, "Checked Out")
    return True
```

---

## Bug 2 — Returning equipment appears to log the user out

**Symptom:** After clicking Return, the "My Equipment" panel goes blank as if the
employee is no longer logged in.

**Root cause — two parts:**

**Part A — `record_return_time()` returns `None` silently on failure.**  
SQLite's `UPDATE` statement does not raise an error when zero rows match — it simply
updates nothing. Because `record_return_time()` never checks `cursor.rowcount`, it
always returns `None`. `ecs_system.py` cannot detect the failure, so `return_equipment()`
always returns `True` even when nothing was actually updated.

**Part B — if Flask returns a 500 error, `script.js` crashes silently.**  
If any unhandled exception occurs in the return route, Flask sends back an HTML error
page. `await res.json()` in `returnEquipment()` then throws because HTML is not valid
JSON, execution jumps to the `catch` block, `refreshLists()` is never called, and the
"My Equipment" panel is left blank from the previous `setContainerContent` wipe — which
looks identical to a logout.

**Fix A — `database_manager.py`**

Add a `rowcount` check to `record_return_time` so callers know whether the update
actually found an open transaction:

```python
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
```

**Fix B — `ecs_system.py`**

Update `return_equipment` to check the result of `record_return_time` before
updating equipment status, and abort early if no open transaction existed:

```python
def return_equipment(self, equipment_id):
    # Try to record the return time first.
    # If no open transaction exists, abort — do not change equipment status.
    updated = self.db_manager.record_return_time(equipment_id)
    if not updated:
        return False   # Flask route sends {"success": false} to the frontend

    self.db_manager.update_equipment_status(equipment_id, "Available")
    return True
```

---

## Bug 3 — "My Equipment" shows duplicate rows after multiple checkouts

**Symptom:** The same item appears more than once in the "My Equipment" panel.

**Root cause:** The SQL query in `get_employee_equipment()` in `database_manager.py`
uses a JOIN between `Equipment` and `Transactions`. If the same item was checked out
more than once (caused by Bug 1 above), there are multiple transaction rows for that
`EquipmentID`. The JOIN returns one result row per matching transaction, producing
duplicates in the rendered list.

**Fix — `database_manager.py`**

Add `DISTINCT` to the SELECT so each piece of equipment appears at most once,
regardless of how many transaction records exist for it:

```python
def get_employee_equipment(self, employee_id):
    conn = self.connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT Equipment.EquipmentID, Equipment.EquipmentName, Equipment.Status
        FROM Equipment
        JOIN Transactions ON Equipment.EquipmentID = Transactions.EquipmentID
        WHERE Transactions.EmployeeID = ? AND Equipment.Status = 'Checked Out'
    """, (employee_id,))
    results = cursor.fetchall()
    conn.close()
    return results
```

> **Note:** Also clean up the bad data already in `ecs.db`. Open the database
> (e.g. with DB Browser for SQLite) and delete the duplicate transaction rows for
> the Drill, then verify the equipment status is correct.

---

## Bug 4 — `returnEquipment()` has no login guard

**Symptom:** In theory a Return request could be sent without an active login session
if the state was somehow lost. The server would still process it.

**Root cause:** Unlike `checkoutEquipment()`, `returnEquipment()` in `script.js` does
not check `currentEmployeeId` before making the API call.

**Fix — `script.js`**

Add the guard at the top of `returnEquipment`:

```javascript
async function returnEquipment(equipmentId) {
    if (!currentEmployeeId) {
        alert('Please log in first');
        return;
    }
    // ... rest of the function unchanged
```

---

## Bug 5 — CSS vendor prefix missing standard `appearance` property

**Symptom:** VS Code shows a warning on line 332 of `style.css`:
> *"Also define the standard property 'appearance' for compatibility"*

**Root cause:** The rule that hides the browser spin arrows on the number input uses
`-moz-appearance: textfield` (a Firefox vendor-prefixed property) without including
the unprefixed standard `appearance` property alongside it. Modern browsers and
linters expect both.

**Fix — `style.css`**

Replace the single-property block with:

```css
input[type="number"] {
    -moz-appearance: textfield;   /* Firefox vendor-prefixed version */
    appearance: textfield;        /* Standard property — required for full compatibility */
}
```

---

## Summary table

| # | File | Method / Location | Issue | Fix |
|---|------|-------------------|-------|-----|
| 1 | `ecs_system.py` | `checkout_equipment()` | No availability check before checkout | Add guard using `get_available_equipment()` |
| 2 | `database_manager.py` | `record_return_time()` | Always returns `None`; silent failure | Return `cursor.rowcount > 0` |
| 2 | `ecs_system.py` | `return_equipment()` | Does not check return value of `record_return_time` | Check result; abort if `False` |
| 3 | `database_manager.py` | `get_employee_equipment()` | JOIN produces duplicate rows | Add `DISTINCT` to SELECT |
| 4 | `script.js` | `returnEquipment()` | No login guard | Add `if (!currentEmployeeId)` check |
| 5 | `style.css` | `input[type="number"]` block | Missing standard `appearance` property | Add `appearance: textfield` |
