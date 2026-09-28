from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..rules_engine import evaluate_campus_access_rules, find_best_spot_for_driver
from ..websocket_manager import ws_manager

router = APIRouter(prefix="/api/parking", tags=["Parking Operations"])


def serialize_spot(spot: models.ParkingSpot, is_authorized_viewer: bool = False) -> schemas.ParkingSpotOut:
    """
    Serializes a parking spot with Data Privacy & RBAC enforcement.
    Public viewers only see spot status (AVAILABLE/OCCUPIED).
    Authorized viewers (ADMIN, SECURITY, FACULTY owner) can see occupant metadata.
    """
    occupant_detail = None
    if spot.status == "OCCUPIED" and spot.current_occupant:
        if is_authorized_viewer:
            plate = spot.current_vehicle.license_plate if spot.current_vehicle else "N/A"
            vtype = spot.current_vehicle.vehicle_type if spot.current_vehicle else "N/A"
            occupant_detail = schemas.OccupantDetail(
                user_id=spot.current_occupant.id,
                name=spot.current_occupant.name,
                role=spot.current_occupant.role,
                department_or_purpose=spot.current_occupant.department_or_purpose,
                license_plate=plate,
                vehicle_type=vtype,
                occupied_at=spot.occupied_at
            )
        else:
            # Masked placeholder for public view - hides personal identity
            occupant_detail = schemas.OccupantDetail(
                user_id=0,
                name="Occupied (Protected)",
                role=spot.current_occupant.role,
                department_or_purpose="Campus Member",
                license_plate="••••-•••",
                vehicle_type=spot.current_vehicle.vehicle_type if spot.current_vehicle else "N/A",
                occupied_at=spot.occupied_at
            )

    return schemas.ParkingSpotOut(
        spot_code=spot.spot_code,
        zone_id=spot.zone_id,
        status=spot.status,
        row_num=spot.row_num,
        col_num=spot.col_num,
        is_ev=spot.is_ev,
        is_accessible=spot.is_accessible,
        distance_to_gate=spot.distance_to_gate,
        occupied_at=spot.occupied_at,
        occupant=occupant_detail
    )


@router.get("/zone/{zone_id}", response_model=schemas.ParkingZoneDetail)
def get_parking_zone_detail(
    zone_id: int,
    db: Annotated[Session, Depends(get_db)],
    x_role: Annotated[str | None, Header()] = None,
    role: Annotated[str | None, Query()] = None
):
    """
    Returns full spot matrix and live status for a specific parking zone.
    Enforces RBAC on occupant details.
    """
    zone = db.query(models.ParkingZone).filter(models.ParkingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Parking zone not found")

    user_role = (x_role or role or "PUBLIC").upper()
    is_authorized = user_role in ["ADMIN", "SECURITY", "ENFORCEMENT"]

    spots = (
        db.query(models.ParkingSpot)
        .filter(models.ParkingSpot.zone_id == zone.id)
        .order_by(models.ParkingSpot.row_num.asc(), models.ParkingSpot.col_num.asc())
        .all()
    )

    occupied_count = sum(1 for s in spots if s.status == "OCCUPIED")
    available_count = zone.total_spots - occupied_count
    occupancy_rate = round((occupied_count / zone.total_spots * 100), 1) if zone.total_spots > 0 else 0.0

    serialized_spots = [serialize_spot(s, is_authorized_viewer=is_authorized) for s in spots]

    return schemas.ParkingZoneDetail(
        id=zone.id,
        zone_code=zone.zone_code,
        zone_name=zone.zone_name,
        allowed_roles=zone.allowed_roles,
        allowed_vehicle_types=zone.allowed_vehicle_types,
        description=zone.description,
        location_label=zone.location_label,
        total_spots=zone.total_spots,
        map_x=zone.map_x,
        map_y=zone.map_y,
        map_width=zone.map_width,
        map_height=zone.map_height,
        accent_color=zone.accent_color,
        available_spots=available_count,
        occupied_spots=occupied_count,
        occupancy_rate=occupancy_rate,
        spots=serialized_spots
    )


@router.post("/suggest", response_model=schemas.SpotSuggestResponse)
def suggest_optimal_spot(
    req: schemas.SpotSuggestRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Accepts { user_id, vehicle_id }, evaluates access control rules,
    and returns the best available spot based on role and vehicle type.
    Strictly denies student 4-wheelers.
    """
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == req.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle.user_id != user.id:
        raise HTTPException(status_code=400, detail="Vehicle does not belong to specified user")

    rule_eval, best_spot, target_zone = find_best_spot_for_driver(db, user, vehicle)

    if not rule_eval.allowed:
        return schemas.SpotSuggestResponse(
            allowed=False,
            rule_code=rule_eval.rule_code,
            message=rule_eval.message,
            best_spot=None,
            target_zone=None,
            eligible_zones=rule_eval.eligible_zone_codes
        )

    # Prepare serialized best spot and zone overview
    best_spot_out = serialize_spot(best_spot, is_authorized_viewer=True) if best_spot else None
    zone_overview = None
    if target_zone:
        occupied = (
            db.query(models.ParkingSpot)
            .filter(models.ParkingSpot.zone_id == target_zone.id, models.ParkingSpot.status == "OCCUPIED")
            .count()
        )
        zone_overview = schemas.ParkingZoneOverview(
            id=target_zone.id,
            zone_code=target_zone.zone_code,
            zone_name=target_zone.zone_name,
            allowed_roles=target_zone.allowed_roles,
            allowed_vehicle_types=target_zone.allowed_vehicle_types,
            description=target_zone.description,
            location_label=target_zone.location_label,
            total_spots=target_zone.total_spots,
            map_x=target_zone.map_x,
            map_y=target_zone.map_y,
            map_width=target_zone.map_width,
            map_height=target_zone.map_height,
            accent_color=target_zone.accent_color,
            available_spots=target_zone.total_spots - occupied,
            occupied_spots=occupied,
            occupancy_rate=round(occupied / target_zone.total_spots * 100, 1) if target_zone.total_spots > 0 else 0.0
        )

    return schemas.SpotSuggestResponse(
        allowed=True,
        rule_code="SUCCESS",
        message=rule_eval.message,
        best_spot=best_spot_out,
        target_zone=zone_overview,
        eligible_zones=rule_eval.eligible_zone_codes
    )


@router.post("/check-in", response_model=schemas.CheckInResponse)
async def check_in_spot(
    req: schemas.CheckInRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Accepts { spot_code, user_id, vehicle_id }, locks spot,
    sets status to OCCUPIED, records timestamp, logs entry,
    and broadcasts instant WebSocket event to all connected dashboards.
    """
    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.spot_code == req.spot_code).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")

    if spot.status == "OCCUPIED":
        raise HTTPException(
            status_code=409,
            detail=f"Spot {req.spot_code} is already occupied. Please select an available spot."
        )

    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == req.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Access rule check for this zone
    zone = spot.zone
    rule_eval = evaluate_campus_access_rules(user, vehicle)
    if not rule_eval.allowed:
        raise HTTPException(status_code=403, detail=rule_eval.message)

    if zone.zone_code not in rule_eval.eligible_zone_codes:
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Spot {spot.spot_code} is in {zone.zone_name}, but your role ({user.role}) is only permitted in {', '.join(rule_eval.eligible_zone_codes)}."
        )

    now = datetime.now(timezone.utc)
    spot.status = "OCCUPIED"
    spot.current_occupant_id = user.id
    spot.current_vehicle_id = vehicle.id
    spot.occupied_at = now

    # Write audit log
    log = models.OccupancyLog(
        spot_code=spot.spot_code,
        user_id=user.id,
        vehicle_id=vehicle.id,
        check_in_time=now,
        check_out_time=None
    )
    db.add(log)
    db.commit()
    db.refresh(spot)

    # Real-time WebSocket broadcast to all clients
    await ws_manager.broadcast({
        "event": "SPOT_OCCUPIED",
        "spot_code": spot.spot_code,
        "zone_id": spot.zone_id,
        "status": "OCCUPIED",
        "occupied_at": now.isoformat(),
        "occupant_role": user.role,
        "vehicle_plate_masked": f"{vehicle.license_plate[:3]}•••"
    })

    serialized_spot = serialize_spot(spot, is_authorized_viewer=True)
    return schemas.CheckInResponse(
        success=True,
        message=f"Vehicle {vehicle.license_plate} checked in to spot {spot.spot_code}.",
        spot_code=spot.spot_code,
        check_in_time=now,
        spot=serialized_spot
    )


@router.post("/check-out", response_model=schemas.CheckOutResponse)
async def check_out_spot(
    req: schemas.CheckOutRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Accepts { spot_code }, clears occupant details, marks spot as AVAILABLE,
    closes the open occupancy log, and broadcasts instant WebSocket event.
    """
    spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.spot_code == req.spot_code).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Parking spot not found")

    if spot.status == "AVAILABLE":
        return schemas.CheckOutResponse(
            success=True,
            message=f"Spot {req.spot_code} is already vacant.",
            spot_code=spot.spot_code,
            vacated_at=datetime.now(timezone.utc),
            duration_minutes=0
        )

    now = datetime.now(timezone.utc)
    duration_min = 0

    # Close latest active occupancy log for this spot
    active_log = (
        db.query(models.OccupancyLog)
        .filter(
            models.OccupancyLog.spot_code == spot.spot_code,
            models.OccupancyLog.check_out_time.is_(None)
        )
        .order_by(models.OccupancyLog.check_in_time.desc())
        .first()
    )

    if active_log:
        active_log.check_out_time = now
        # Calculate duration
        start = active_log.check_in_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        diff = now - start
        duration_min = int(diff.total_seconds() // 60)

    spot.status = "AVAILABLE"
    spot.current_occupant_id = None
    spot.current_vehicle_id = None
    spot.occupied_at = None

    db.commit()

    # Real-time WebSocket broadcast to all clients
    await ws_manager.broadcast({
        "event": "SPOT_VACATED",
        "spot_code": spot.spot_code,
        "zone_id": spot.zone_id,
        "status": "AVAILABLE",
        "vacated_at": now.isoformat()
    })

    return schemas.CheckOutResponse(
        success=True,
        message=f"Spot {spot.spot_code} vacated and restored to green available status.",
        spot_code=spot.spot_code,
        vacated_at=now,
        duration_minutes=duration_min
    )
