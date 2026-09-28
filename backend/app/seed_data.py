from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from . import models
from .database import Base, engine


def init_db_and_seed(db: Session):
    Base.metadata.create_all(bind=engine)

    # Check if already seeded
    if db.query(models.ParkingZone).first():
        return

    print("[SEED] Seeding College Campus Parking Management Platform...")

    # 1. Seed Users
    users_data = [
        # Faculty & Admin
        {"name": "Dr. Sarah Mitchell", "phone": "+1-555-0101", "role": "FACULTY", "department_or_purpose": "Dept of Computer Science"},
        {"name": "Prof. David Zhang", "phone": "+1-555-0102", "role": "FACULTY", "department_or_purpose": "Dept of Electrical Engg"},
        {"name": "Dr. Elena Rostova", "phone": "+1-555-0103", "role": "FACULTY", "department_or_purpose": "Dept of Physics"},
        {"name": "Marcus Vance", "phone": "+1-555-0104", "role": "ADMIN", "department_or_purpose": "Dean of Academic Affairs"},
        {"name": "Rachel Adams", "phone": "+1-555-0105", "role": "ADMIN", "department_or_purpose": "Registrar Office"},

        # Students
        {"name": "Liam Parker", "phone": "+1-555-0201", "role": "STUDENT", "department_or_purpose": "Undergraduate B.Tech CS (Yr 3)"},
        {"name": "Maya Patel", "phone": "+1-555-0202", "role": "STUDENT", "department_or_purpose": "Mechanical Engineering (Yr 4)"},
        {"name": "Chloe Bennett", "phone": "+1-555-0203", "role": "STUDENT", "department_or_purpose": "School of Management (Yr 2)"},
        {"name": "Ethan Cole", "phone": "+1-555-0204", "role": "STUDENT", "department_or_purpose": "Civil Engineering (Yr 1)"},

        # Visitors
        {"name": "Dr. Arthur Pendelton", "phone": "+1-555-0301", "role": "VISITOR", "department_or_purpose": "Keynote Speaker - AI Symposium"},
        {"name": "Sophia Martinez", "phone": "+1-555-0302", "role": "VISITOR", "department_or_purpose": "Accreditation Inspector"},
        {"name": "James Henderson", "phone": "+1-555-0303", "role": "VISITOR", "department_or_purpose": "Parent / Campus Tour"},

        # Security
        {"name": "Chief Security Officer Miller", "phone": "+1-555-0999", "role": "ADMIN", "department_or_purpose": "Campus Security & Enforcement"},
    ]

    users = {}
    for u_data in users_data:
        u = models.User(**u_data)
        db.add(u)
        db.flush()
        users[u.name] = u

    # 2. Seed Vehicles
    vehicles_data = [
        # Faculty Vehicles (Mix of 4W and 2W)
        {"user": "Dr. Sarah Mitchell", "plate": "CAMPUS-F4W-10", "type": "FOUR_WHEELER"},
        {"user": "Prof. David Zhang", "plate": "CAMPUS-F2W-22", "type": "TWO_WHEELER"},
        {"user": "Dr. Elena Rostova", "plate": "CAMPUS-F4W-15", "type": "FOUR_WHEELER"},
        {"user": "Marcus Vance", "plate": "ADMIN-4W-01", "type": "FOUR_WHEELER"},
        {"user": "Rachel Adams", "plate": "ADMIN-2W-09", "type": "TWO_WHEELER"},

        # Student Vehicles
        {"user": "Liam Parker", "plate": "STUD-2W-881", "type": "TWO_WHEELER"},
        {"user": "Maya Patel", "plate": "STUD-2W-404", "type": "TWO_WHEELER"},
        {"user": "Chloe Bennett", "plate": "STUD-4W-999", "type": "FOUR_WHEELER"},  # Rule Violation Test Subject!
        {"user": "Ethan Cole", "plate": "STUD-2W-112", "type": "TWO_WHEELER"},

        # Visitor Vehicles
        {"user": "Dr. Arthur Pendelton", "plate": "VIS-4W-771", "type": "FOUR_WHEELER"},
        {"user": "Sophia Martinez", "plate": "VIS-4W-550", "type": "FOUR_WHEELER"},
        {"user": "James Henderson", "plate": "VIS-2W-330", "type": "TWO_WHEELER"},
    ]

    vehicles = {}
    for v_data in vehicles_data:
        v = models.Vehicle(
            user_id=users[v_data["user"]].id,
            license_plate=v_data["plate"],
            vehicle_type=v_data["type"]
        )
        db.add(v)
        db.flush()
        vehicles[v_data["user"]] = v

    # 3. Seed Parking Zones
    zones_def = [
        {
            "zone_code": "FACULTY_4W",
            "zone_name": "Faculty & Admin 4-Wheeler Bay",
            "allowed_roles": "FACULTY,ADMIN",
            "allowed_vehicle_types": "FOUR_WHEELER",
            "description": "Premium shaded 4-wheeler parking reserved strictly for faculty members, deans, and senior university administrative officers.",
            "location_label": "North Quad • Adjacent to Admin Block",
            "total_spots": 16,
            "map_x": 160,
            "map_y": 90,
            "map_width": 210,
            "map_height": 135,
            "accent_color": "#38bdf8",  # Sky Blue
            "prefix": "F4W",
            "rows": 2,
            "cols": 8
        },
        {
            "zone_code": "FACULTY_2W",
            "zone_name": "Faculty & Admin 2-Wheeler Shed",
            "allowed_roles": "FACULTY,ADMIN",
            "allowed_vehicle_types": "TWO_WHEELER",
            "description": "Covered two-wheeler parking shed for faculty motorcycles, scooters, and electric bikes with direct access to STEM corridors.",
            "location_label": "East Wing • Near Science & Tech Hub",
            "total_spots": 20,
            "map_x": 640,
            "map_y": 95,
            "map_width": 210,
            "map_height": 135,
            "accent_color": "#a855f7",  # Purple
            "prefix": "F2W",
            "rows": 2,
            "cols": 10
        },
        {
            "zone_code": "STUDENT_2W",
            "zone_name": "Student 2-Wheeler Plaza",
            "allowed_roles": "STUDENT",
            "allowed_vehicle_types": "TWO_WHEELER",
            "description": "High-capacity student motorcycle & scooter park with wide drive lanes and proximity to library, cafeteria, and sports complex.",
            "location_label": "South Quad • Near Central Library & Cafeteria",
            "total_spots": 24,
            "map_x": 220,
            "map_y": 420,
            "map_width": 250,
            "map_height": 140,
            "accent_color": "#10b981",  # Emerald Green
            "prefix": "S2W",
            "rows": 3,
            "cols": 8
        },
        {
            "zone_code": "VISITOR_PARKING",
            "zone_name": "Visitor & Guest Parking Bay",
            "allowed_roles": "VISITOR,FACULTY,ADMIN",
            "allowed_vehicle_types": "TWO_WHEELER,FOUR_WHEELER",
            "description": "Designated welcome parking bay for registered campus guests, visiting lecturers, inspectors, and overflow university staff.",
            "location_label": "Main Gate • Reception & Security Checkpoint",
            "total_spots": 16,
            "map_x": 600,
            "map_y": 420,
            "map_width": 220,
            "map_height": 140,
            "accent_color": "#f59e0b",  # Amber
            "prefix": "VIS",
            "rows": 2,
            "cols": 8
        },
    ]

    spots_map = {}
    for z_data in zones_def:
        zone = models.ParkingZone(
            zone_code=z_data["zone_code"],
            zone_name=z_data["zone_name"],
            allowed_roles=z_data["allowed_roles"],
            allowed_vehicle_types=z_data["allowed_vehicle_types"],
            description=z_data["description"],
            location_label=z_data["location_label"],
            total_spots=z_data["total_spots"],
            map_x=z_data["map_x"],
            map_y=z_data["map_y"],
            map_width=z_data["map_width"],
            map_height=z_data["map_height"],
            accent_color=z_data["accent_color"]
        )
        db.add(zone)
        db.flush()

        spot_counter = 1
        for r in range(1, z_data["rows"] + 1):
            for c in range(1, z_data["cols"] + 1):
                if spot_counter > z_data["total_spots"]:
                    break
                code = f"{z_data['prefix']}-{spot_counter:02d}"
                is_ev = (spot_counter in [1, 2])
                is_acc = (spot_counter in [3])
                # Calculate distance score (lower is closer to entrance)
                distance = (r - 1) * 5 + c * 2

                spot = models.ParkingSpot(
                    spot_code=code,
                    zone_id=zone.id,
                    status="AVAILABLE",
                    row_num=r,
                    col_num=c,
                    is_ev=is_ev,
                    is_accessible=is_acc,
                    distance_to_gate=distance
                )
                db.add(spot)
                spots_map[code] = spot
                spot_counter += 1

    db.flush()

    # 4. Seed Some Initial Occupants to make the map look active and alive
    initial_occupancies = [
        {"spot": "F4W-02", "user": "Dr. Sarah Mitchell", "hours_ago": 2.5},
        {"spot": "F4W-05", "user": "Marcus Vance", "hours_ago": 4.1},
        {"spot": "F2W-03", "user": "Prof. David Zhang", "hours_ago": 1.2},
        {"spot": "F2W-07", "user": "Rachel Adams", "hours_ago": 3.0},
        {"spot": "S2W-01", "user": "Liam Parker", "hours_ago": 0.8},
        {"spot": "S2W-04", "user": "Maya Patel", "hours_ago": 2.1},
        {"spot": "S2W-09", "user": "Ethan Cole", "hours_ago": 1.5},
        {"spot": "VIS-02", "user": "Dr. Arthur Pendelton", "hours_ago": 1.9},
        {"spot": "VIS-06", "user": "James Henderson", "hours_ago": 0.4},
    ]

    now = datetime.now(timezone.utc)
    for occ in initial_occupancies:
        code = occ["spot"]
        user_obj = users[occ["user"]]
        veh_obj = vehicles[occ["user"]]
        check_in_time = now - timedelta(hours=occ["hours_ago"])

        if code in spots_map:
            spot = spots_map[code]
            spot.status = "OCCUPIED"
            spot.current_occupant_id = user_obj.id
            spot.current_vehicle_id = veh_obj.id
            spot.occupied_at = check_in_time

            log = models.OccupancyLog(
                spot_code=code,
                user_id=user_obj.id,
                vehicle_id=veh_obj.id,
                check_in_time=check_in_time,
                check_out_time=None
            )
            db.add(log)

    # Add a couple of past completed logs for audit enforcement demonstration
    past_logs = [
        {"spot": "F4W-01", "user": "Dr. Elena Rostova", "in_h": 6, "out_h": 2},
        {"spot": "VIS-01", "user": "Sophia Martinez", "in_h": 5, "out_h": 1.5},
    ]
    for pl in past_logs:
        user_obj = users[pl["user"]]
        veh_obj = vehicles[pl["user"]]
        cin = now - timedelta(hours=pl["in_h"])
        cout = now - timedelta(hours=pl["out_h"])
        db.add(models.OccupancyLog(
            spot_code=pl["spot"],
            user_id=user_obj.id,
            vehicle_id=veh_obj.id,
            check_in_time=cin,
            check_out_time=cout
        ))

    db.commit()
    print("[SUCCESS] Campus zones, spots, test users, and initial occupancy logs seeded successfully.")
