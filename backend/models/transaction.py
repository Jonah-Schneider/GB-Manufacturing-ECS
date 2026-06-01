class Transaction:
    def __init__(self, transaction_id, employee_id, equipment_id, checkout_time, return_time=None):
        self.transaction_id = transaction_id
        self.employee_id = employee_id
        self.equipment_id = equipment_id
        self.checkout_time = checkout_time
        self.return_time = return_time
