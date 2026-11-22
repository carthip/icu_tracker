"""
Seed data: simulated hospitals and ambulances.
All coordinates are illustrative (Chennai, India region).
"""

HOSPITALS = [
    {
        "id": "H001",
        "name": "Apollo Hospital",
        "lat": 13.0604,
        "lon": 80.2496,
        "icu_total": 20,
        "icu_available": 5,
    },
    {
        "id": "H002",
        "name": "Fortis Malar Hospital",
        "lat": 13.0012,
        "lon": 80.2565,
        "icu_total": 15,
        "icu_available": 0,
    },
    {
        "id": "H003",
        "name": "MIOT International",
        "lat": 13.0314,
        "lon": 80.1753,
        "icu_total": 25,
        "icu_available": 8,
    },
    {
        "id": "H004",
        "name": "Kauvery Hospital",
        "lat": 13.0732,
        "lon": 80.2609,
        "icu_total": 18,
        "icu_available": 2,
    },
    {
        "id": "H005",
        "name": "Sri Ramachandra Hospital",
        "lat": 13.0356,
        "lon": 80.1548,
        "icu_total": 30,
        "icu_available": 12,
    },
]

AMBULANCES = [
    {
        "id": "AMB001",
        "name": "Ambulance Alpha",
        "lat": 13.0550,
        "lon": 80.2300,
        "status": "available",   # available | dispatched | returning
        "assigned_to": None,
    },
    {
        "id": "AMB002",
        "name": "Ambulance Bravo",
        "lat": 13.0200,
        "lon": 80.2600,
        "status": "dispatched",
        "assigned_to": "H002",
    },
    {
        "id": "AMB003",
        "name": "Ambulance Charlie",
        "lat": 13.0400,
        "lon": 80.1900,
        "status": "available",
        "assigned_to": None,
    },
    {
        "id": "AMB004",
        "name": "Ambulance Delta",
        "lat": 13.0700,
        "lon": 80.2700,
        "status": "returning",
        "assigned_to": None,
    },
    {
        "id": "AMB005",
        "name": "Ambulance Echo",
        "lat": 13.0100,
        "lon": 80.2100,
        "status": "available",
        "assigned_to": None,
    },
]
