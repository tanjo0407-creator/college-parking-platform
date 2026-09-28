from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/campus", tags=["Campus Overview"])

# Campus buildings coordinates and metadata for rich 2D map visualization
CAMPUS_BUILDINGS = [
    {
        "id": "bldg-admin",
        "name": "Administration Complex & Senate",
        "category": "academic",
        "x": 120,
        "y": 240,
        "width": 260,
        "height": 130,
        "label": "ADMINISTRATION",
        "icon": "building",
        "color": "#1e293b"
    },
    {
        "id": "bldg-stem",
        "name": "School of Engineering & STEM Labs",
        "category": "academic",
        "x": 620,
        "y": 240,
        "width": 260,
        "height": 130,
        "label": "STEM & TECH LABS",
        "icon": "cpu",
        "color": "#1e293b"
    },
    {
        "id": "bldg-library",
        "name": "Central University Library & Innovation Hub",
        "category": "facility",
        "x": 420,
        "y": 190,
        "width": 160,
        "height": 220,
        "label": "CENTRAL LIBRARY",
        "icon": "book-open",
        "color": "#0f172a"
    },
    {
        "id": "bldg-student-hub",
        "name": "Student Center, Cafeteria & Gymnasium",
        "category": "facility",
        "x": 180,
        "y": 590,
        "width": 300,
        "height": 90,
        "label": "STUDENT COMMONS & CAFETERIA",
        "icon": "coffee",
        "color": "#1e293b"
    },
    {
        "id": "gate-main",
        "name": "Campus Main Entrance & Security Checkpoint",
        "category": "gate",
        "x": 580,
        "y": 620,
        "width": 260,
        "height": 60,
        "label": "MAIN GATE & VISITOR SECURITY",
        "icon": "shield-check",
        "color": "#334155"
    }
]


@router.get("/overview", response_model=schemas.CampusOverviewResponse)
def get_campus_overview(db: Annotated[Session, Depends(get_db)]):
    """
    Returns high-level visual Overview Map data of the entire college campus
    showing locations of all parking areas and real-time occupancy counts.
    """
    zones = db.query(models.ParkingZone).all()

    zone_overviews = []
    total_campus_spots = 0
    total_campus_occupied = 0

    for z in zones:
        total_spots = z.total_spots
        occupied_count = (
            db.query(models.ParkingSpot)
            .filter(
                models.ParkingSpot.zone_id == z.id,
                models.ParkingSpot.status == "OCCUPIED"
            )
            .count()
        )
        available_count = total_spots - occupied_count
        occupancy_rate = round((occupied_count / total_spots * 100), 1) if total_spots > 0 else 0.0

        total_campus_spots += total_spots
        total_campus_occupied += occupied_count

        zone_overviews.append(
            schemas.ParkingZoneOverview(
                id=z.id,
                zone_code=z.zone_code,
                zone_name=z.zone_name,
                allowed_roles=z.allowed_roles,
                allowed_vehicle_types=z.allowed_vehicle_types,
                description=z.description,
                location_label=z.location_label,
                total_spots=total_spots,
                map_x=z.map_x,
                map_y=z.map_y,
                map_width=z.map_width,
                map_height=z.map_height,
                accent_color=z.accent_color,
                available_spots=available_count,
                occupied_spots=occupied_count,
                occupancy_rate=occupancy_rate
            )
        )

    available_campus_spots = total_campus_spots - total_campus_occupied
    overall_occupancy_rate = (
        round((total_campus_occupied / total_campus_spots * 100), 1)
        if total_campus_spots > 0 else 0.0
    )

    metrics = schemas.CampusMetrics(
        total_spots=total_campus_spots,
        available_spots=available_campus_spots,
        occupied_spots=total_campus_occupied,
        overall_occupancy_rate=overall_occupancy_rate
    )

    return schemas.CampusOverviewResponse(
        metrics=metrics,
        zones=zone_overviews,
        buildings=CAMPUS_BUILDINGS,
        server_time=datetime.now(timezone.utc)
    )
