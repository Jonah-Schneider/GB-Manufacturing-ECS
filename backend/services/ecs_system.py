class ECSSystem:

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def login_employee(self, employee_id):
        pass

    def get_available_equipment(self):
        pass

    def checkout_equipment(self, employee_id, equipment_id):
        pass
    
    #used to view what equipment the individual employee has checkout out. 
    def get_employee_equipment(self, employee_id):
        pass 
    def return_equipment(self, equipment_id):
        pass

    def get_transactions(self):
        pass