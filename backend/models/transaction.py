# Class to store Data for Transactions that occur so they can be updated to SQL and viewed, includes transaction_id value, employee_id (the one who check the item out)
#It also includes the id for the equipment being taken out, the time of checkout, and the time that it was returned. 
#return_time is set to a default of None because an item can be taken out and not returned yet, by ensuring return_time is None to start we can prevent possible errors.

class Transaction:
    def __init__(self, transaction_id, employee_id, equipment_id, checkout_time, return_time=None):
        self.transaction_id = transaction_id
        self.employee_id = employee_id
        self.equipment_id = equipment_id
        self.checkout_time = checkout_time
        self.return_time = return_time
