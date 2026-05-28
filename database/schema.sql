CREATE TABLE Employees (
    EmployeeID INTEGER PRIMARY KEY,
    FullName TEXT
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

INSERT INTO Employees (EmployeeID, FullName)
VALUES 
(1001, 'Jonah Schneider'),
(1002, 'Michael Mottie'),
(1003, 'Adriel Spencer'),
(1004, 'Clinton Hockenberry'),
(1005, 'Anthony Dumsar');


INSERT INTO Equipment (EquipmentID, EquipmentName, Status)
VALUES
(2001, 'Drill', 'Available'),
(2002, 'Hammer', 'Available'),
(2003, 'Wrench', 'Available'),
(2004, 'Saw', 'Available'),
(2005, 'Ladder', 'Available'),
(2006, 'Toolbox', 'Available'),
(2007, 'Safety Helmet', 'Available');