from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..rules_engine import find_best_spot_for_driver

router = APIRouter(prefix="/api/visitors", tags=["Visitor Management"])


@router.post("/register")
def register_visitor(
    req: schemas.VisitorRegisterRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Quick self-service or gate check-in registration for campus visitors.
    Creates User + Vehicle and automatically suggests an optimal spot in VISITOR_PARKING.
    """
    vtype = req.vehicle_type.upper()
    if vtype not in ["TWO_WHEELER", "FOUR_WHEELER"]:
        raise HTTPException(status_code=400, detail="Vehicle type must be TWO_WHEELER or FOUR_WHEELER")

    # Check if plate already registered
    existing_vehicle = db.query(models.Vehicle).filter(models.Vehicle.license_plate == req.license_plate.upper()).first()
    if existing_vehicle:
        user = existing_vehicle.owner
        vehicle = existing_vehicle
    else:
        # Create Visitor User
        user = models.User(
            name=req.name,
            phone=req.phone,
            role="VISITOR",
            department_or_purpose=req.purpose or "Guest Visitor"
        )
        db.add(user)
        db.flush()

        # Create Vehicle
        vehicle = models.Vehicle(
            user_id=user.id,
            license_plate=req.license_plate.upper(),
            vehicle_type=vtype
        )
        db.add(vehicle)
        db.commit()
        db.refresh(user)
        db.refresh(vehicle)

    # Automatically find best spot for this visitor
    rule_eval, best_spot, target_zone = find_best_spot_for_driver(db, user, vehicle)

    return {
        "success": True,
        "message": f"Visitor {user.name} successfully registered.",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "purpose": user.department_or_purpose
        },
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type
        },
        "assigned_zone": target_zone.zone_code if target_zone else "VISITOR_PARKING",
        "suggested_spot": best_spot.spot_code if best_spot else None,
        "rule_message": rule_eval.message
    }
