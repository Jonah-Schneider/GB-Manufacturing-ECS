CREATE TABLE Employees (
    EmployeeID INTEGER PRIMARY KEY,
    Name TEXT
);

CREATE TABLE Equipment (
    EquipmentID INTEGER PRIMARY KEY,
    EquipmentName TEXT,
    Status TEXT
);

CREATE TABLE Transactions (
    TransactionID INTEGER PRIMARY KEY,
    EmployeeID INTEGER,
    EquipmentID INTEGER,
    CheckoutTime TEXT,
    ReturnTime TEXT
);