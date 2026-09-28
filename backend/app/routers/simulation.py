import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..websocket_manager import ws_manager

router = APIRouter(prefix="/api/simulation", tags=["Simulation Controls"])


@router.post("/random-event")
async def trigger_random_parking_event(db: Session = Depends(get_db)):
    """
    Simulates a random realistic vehicle arrival (check-in) or departure (check-out)
    to demonstrate live real-time map synchronization.
    """
    # Decide whether to check-in or check-out (50/50, or biased by available vs occupied count)
    occupied_spots = db.query(models.ParkingSpot).filter(models.ParkingSpot.status == "OCCUPIED").all()
    available_spots = db.query(models.ParkingSpot).filter(models.ParkingSpot.status == "AVAILABLE").all()

    action = "CHECK_IN"
    if occupied_spots and available_spots:
        action = random.choice(["CHECK_IN", "CHECK_OUT"])
    elif occupied_spots and not available_spots:
        action = "CHECK_OUT"
    elif available_spots and not occupied_spots:
        action = "CHECK_IN"
    else:
        return {"status": "NO_OP", "message": "No spots available to simulate"}

    now = datetime.now(timezone.utc)

    if action == "CHECK_IN" and available_spots:
        spot = random.choice(available_spots)
        zone = spot.zone

        # Find eligible user/vehicle matching this zone
        eligible_users = (
            db.query(models.User)
            .join(models.Vehicle)
            .filter(models.Vehicle.user_id == models.User.id)
            .all()
        )
        # Filter for valid users based on zone allowed roles and vehicle types
        allowed_roles = [r.strip().upper() for r in zone.allowed_roles.split(",")]
        allowed_vtypes = [v.strip().upper() for v in zone.allowed_vehicle_types.split(",")]

        valid_pairs = []
        for u in eligible_users:
            if u.role.upper() in allowed_roles:
                for v in u.vehicles:
                    if v.vehicle_type.upper() in allowed_vtypes:
                        # Extra rule: student with four-wheeler never permitted
                        if u.role.upper() == "STUDENT" and v.vehicle_type.upper() == "FOUR_WHEELER":
                            continue
                        valid_pairs.append((u, v))

        if not valid_pairs:
            # Fallback to demo guest
            user = models.User(name=f"Guest_{random.randint(100, 999)}", phone="+1-555-0000", role="VISITOR", department_or_purpose="Campus Visitor")
            db.add(user)
            db.flush()
            vtype = random.choice(allowed_vtypes)
            vehicle = models.Vehicle(user_id=user.id, license_plate=f"SIM-{random.randint(1000, 9999)}", vehicle_type=vtype)
            db.add(vehicle)
            db.flush()
        else:
            user, vehicle = random.choice(valid_pairs)

        spot.status = "OCCUPIED"
        spot.current_occupant_id = user.id
        spot.current_vehicle_id = vehicle.id
        spot.occupied_at = now

        log = models.OccupancyLog(
            spot_code=spot.spot_code,
            user_id=user.id,
            vehicle_id=vehicle.id,
            check_in_time=now,
            check_out_time=None
        )
        db.add(log)
        db.commit()

        await ws_manager.broadcast({
            "event": "SPOT_OCCUPIED",
            "spot_code": spot.spot_code,
            "zone_id": spot.zone_id,
            "status": "OCCUPIED",
            "occupied_at": now.isoformat(),
            "occupant_role": user.role,
            "vehicle_plate_masked": f"{vehicle.license_plate[:3]}•••"
        })

        return {
            "status": "CHECK_IN_SUCCESS",
            "action": "CHECK_IN",
            "spot_code": spot.spot_code,
            "zone_code": zone.zone_code,
            "user": user.name,
            "role": user.role,
            "vehicle_plate": vehicle.license_plate,
            "timestamp": now.isoformat()
        }

    elif action == "CHECK_OUT" and occupied_spots:
        spot = random.choice(occupied_spots)
        zone = spot.zone
        spot_code = spot.spot_code

        # Close active log
        active_log = (
            db.query(models.OccupancyLog)
            .filter(
                models.OccupancyLog.spot_code == spot_code,
                models.OccupancyLog.check_out_time.is_(None)
            )
            .order_by(models.OccupancyLog.check_in_time.desc())
            .first()
        )
        if active_log:
            active_log.check_out_time = now

        spot.status = "AVAILABLE"
        spot.current_occupant_id = None
        spot.current_vehicle_id = None
        spot.occupied_at = None
        db.commit()

        await ws_manager.broadcast({
            "event": "SPOT_VACATED",
            "spot_code": spot_code,
            "zone_id": zone.id,
            "status": "AVAILABLE",
            "vacated_at": now.isoformat()
        })

        return {
            "status": "CHECK_OUT_SUCCESS",
            "action": "CHECK_OUT",
            "spot_code": spot_code,
            "zone_code": zone.zone_code,
            "timestamp": now.isoformat()
        }


@router.post("/reset")
async def reset_simulation_state(db: Session = Depends(get_db)):
    """
    Clears all active occupancies and restores spots to available state.
    """
    occupied_spots = db.query(models.ParkingSpot).filter(models.ParkingSpot.status == "OCCUPIED").all()
    now = datetime.now(timezone.utc)

    for spot in occupied_spots:
        spot.status = "AVAILABLE"
        spot.current_occupant_id = None
        spot.current_vehicle_id = None
        spot.occupied_at = None

    # Close any open logs
    db.query(models.OccupancyLog).filter(models.OccupancyLog.check_out_time.is_(None)).update(
        {"check_out_time": now}
    )

    db.commit()

    await ws_manager.broadcast({
        "event": "CAMPUS_RESET",
        "timestamp": now.isoformat()
    })

    return {"status": "SUCCESS", "message": "All parking spots reset to VACANT."}
