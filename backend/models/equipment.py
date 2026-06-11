# Class to store Data for equipment's within an object including equipment_id, equipment_name, and it's checkout status. It includes an _init_ command to set up the class. 

class Equipment:
    def __init__(self, equipment_id, equipment_name, status):
        self.equipment_id = equipment_id
        self.equipment_name = equipment_name
        self.status = status
    