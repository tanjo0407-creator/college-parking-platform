from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..rules_engine import find_best_spot_for_driver

router = APIRouter(prefix="/api", tags=["Users & Security Logs"])


@router.get("/users", response_model=list[schemas.UserOut])
def get_all_users(db: Annotated[Session, Depends(get_db)]):
    """
    Returns list of seeded users with their registered vehicles for quick profile switching and testing.
    """
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@router.post("/users/register")
def register_new_user(
    req: schemas.UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Registers a new campus user with any role (FACULTY, ADMIN, STUDENT, VISITOR) and vehicle.
    Evaluates campus access rules and automatically calculates optimal spot.
    """
    role = req.role.strip().upper()
    if role not in ["FACULTY", "ADMIN", "STUDENT", "VISITOR"]:
        raise HTTPException(status_code=400, detail="Role must be FACULTY, ADMIN, STUDENT, or VISITOR")

    vtype = req.vehicle_type.strip().upper()
    if vtype not in ["TWO_WHEELER", "FOUR_WHEELER"]:
        raise HTTPException(status_code=400, detail="Vehicle type must be TWO_WHEELER or FOUR_WHEELER")

    # Create User
    user = models.User(
        name=req.name.strip(),
        phone=req.phone.strip(),
        role=role,
        department_or_purpose=req.department_or_purpose.strip() or "Campus Member"
    )
    db.add(user)
    db.flush()

    # Create Vehicle
    plate = req.license_plate.strip().upper()
    # Check if plate already registered
    existing_veh = db.query(models.Vehicle).filter(models.Vehicle.license_plate == plate).first()
    if existing_veh:
        existing_veh.user_id = user.id
        existing_veh.vehicle_type = vtype
        vehicle = existing_veh
    else:
        vehicle = models.Vehicle(
            user_id=user.id,
            license_plate=plate,
            vehicle_type=vtype
        )
        db.add(vehicle)

    db.commit()
    db.refresh(user)
    db.refresh(vehicle)

    # Evaluate access rules
    rule_eval, best_spot, target_zone = find_best_spot_for_driver(db, user, vehicle)

    return {
        "success": True,
        "message": f"User {user.name} ({user.role}) successfully registered with vehicle {vehicle.license_plate}.",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "department": user.department_or_purpose
        },
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type
        },
        "rule_evaluation": {
            "allowed": rule_eval.allowed,
            "rule_code": rule_eval.rule_code,
            "message": rule_eval.message,
            "eligible_zones": rule_eval.eligible_zone_codes
        },
        "target_zone": {
            "id": target_zone.id,
            "zone_code": target_zone.zone_code,
            "zone_name": target_zone.zone_name
        } if target_zone else None,
        "suggested_spot": best_spot.spot_code if best_spot else None
    }


@router.get("/logs", response_model=list[schemas.OccupancyLogOut])
def get_occupancy_logs(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    spot_code: Annotated[str | None, Query()] = None,
    x_role: Annotated[str | None, Header()] = None,
    role: Annotated[str | None, Query()] = None
):
    """
    Returns secure campus parking occupancy and enforcement logs.
    Shows check-in and check-out timestamps, vehicle plate, user details, and duration.
    """
    query = db.query(models.OccupancyLog).order_by(models.OccupancyLog.check_in_time.desc())

    if spot_code:
        query = query.filter(models.OccupancyLog.spot_code == spot_code)

    logs = query.limit(limit).all()

    result = []
    now = datetime.now(timezone.utc)
    for log in logs:
        # Calculate duration
        start = log.check_in_time
        if start and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        duration = None
        if log.check_out_time:
            end = log.check_out_time
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            duration = int((end - start).total_seconds() // 60)
        elif start:
            duration = int((now - start).total_seconds() // 60)

        result.append(
            schemas.OccupancyLogOut(
                id=log.id,
                spot_code=log.spot_code,
                user_id=log.user_id,
                user_name=log.user.name if log.user else "Unknown User",
                user_role=log.user.role if log.user else "UNKNOWN",
                user_department=log.user.department_or_purpose if log.user else "N/A",
                license_plate=log.vehicle.license_plate if log.vehicle else "N/A",
                vehicle_type=log.vehicle.vehicle_type if log.vehicle else "N/A",
                check_in_time=log.check_in_time,
                check_out_time=log.check_out_time,
                duration_minutes=duration
            )
        )

    return result
