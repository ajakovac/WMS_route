from mongo import get_db
import json
import hashlib
from datetime import datetime

db = get_db()

warehouses = db["warehouses"]
locations = db["warehouselocations"]
for warehouse in warehouses.find():
    id = warehouse["_id"]
    with open("output.txt", "a") as f:
        json.dump(warehouse, f, default=str)
        f.write("\n")        

newwarehouse = {
    "name": "Test Warehouse",
    "key": hashlib.sha256("Test Warehouse".encode()).hexdigest(),
    "description": "This is a test warehouse",
    "warehouseType": "Distribution Center",
    "status": "ACTIVE",
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "postalCode": "12345",
        "country": "USA"},
    'capacity': {
        'totalSquareMeters': 100000,
        'storageSquareMeters': 9500,
        'totalCubicMeters': 0,
        'maxPalletPositions': 40,
        'totalLocations': 40, 
        'temperatureControlled': False}, 
    'layout': {
        'rows': 2,
        'baysPerRow': 20,
        'cellsPerBay': 1,
        'tiersPerCell': 1,
        'aisleWidth': 30,
        'ceilingHeight': None,
        'isOpenAir': False,
        'zones': [],
        'totalPalletCapacity': 40},
    'capabilities': ['RECEIVING', 'SHIPPING', 'BULK_HANDLING'],
    'operatingHours': {
        'monday': {'isOpen': True, 'openTime': '08:00', 'closeTime': '17:00'},
        'tuesday': {'isOpen': True, 'openTime': '08:00', 'closeTime': '17:00'},
        'wednesday': {'isOpen': True, 'openTime': '08:00', 'closeTime': '17:00'},
        'thursday': {'isOpen': True, 'openTime': '08:00', 'closeTime': '17:00'},
        'friday': {'isOpen': True, 'openTime': '08:00', 'closeTime': '17:00'},
        'saturday': {'isOpen': False},
        'sunday': {'isOpen': False},
        'holidays': []
    },
    'managerId': '834afc4cf5c88ac49a3eb9db',
    'additionalEmployeeIds': ['8db2b3aa73655bcd80605f01'],
    'departmentId': '',
    'contactInfo': {
        'phoneNumber': '+36707441235',
        'email': 'fkocsis@tiszasoft.com',
        'emergencyContact': '',
        'faxNumber': ''
    },
    'organizationId': '01KKEH5NV0MCK1MYFN2K7VKSSS',
    'isActive': True,
    'archived': False,
    'version': 3,
    'createdAt': datetime(2025, 10, 8, 15, 42, 42, 243000),
    'updatedAt': datetime(2025, 10, 8, 16, 52, 9, 234000),
    'createdBy': 'admin@tiszasoft.com',
    'updatedBy': 'admin@tiszasoft.com',
    '__v': 1
}