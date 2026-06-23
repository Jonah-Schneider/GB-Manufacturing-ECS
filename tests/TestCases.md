# How to run tests:
pip install pytest
pytest
make sure to use cd backend in console
use command: python -m pytest ../tests/test_ecs.py -v
# Test Cases

## Login Test

Objective:
Verify employee login functionality.

Expected Result:
Employee successfully accesses system dashboard.

---

## Checkout Test

Objective:
Verify equipment can be checked out.

Expected Result:
Equipment status changes to checked out.

---

## Return Test

Objective:
Verify equipment can be returned.

Expected Result:
Equipment status changes to available.