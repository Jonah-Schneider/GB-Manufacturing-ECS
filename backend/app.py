#Testing the connection of the database_manager with the actual database using a test_connection method in the databaseManager class/may delete at a later point. 
from services.database_manager import DatabaseManager

db_manager = DatabaseManager("database/ecs.db")

db_manager.test_connection()

