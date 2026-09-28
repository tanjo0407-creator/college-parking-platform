from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # FACULTY, ADMIN, STUDENT, VISITOR
    department_or_purpose: Mapped[str] = mapped_column(String(100), nullable=False)

    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    occupancy_logs: Mapped[list["OccupancyLog"]] = relationship("OccupancyLog", back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    license_plate: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # TWO_WHEELER, FOUR_WHEELER

    owner: Mapped["User"] = relationship("User", back_populates="vehicles")
    occupancy_logs: Mapped[list["OccupancyLog"]] = relationship("OccupancyLog", back_populates="vehicle")


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    zone_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)  # e.g. FACULTY_4W
    zone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allowed_roles: Mapped[str] = mapped_column(String(255), nullable=False)  # comma separated: FACULTY,ADMIN
    allowed_vehicle_types: Mapped[str] = mapped_column(String(255), nullable=False)  # comma separated: FOUR_WHEELER
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_spots: Mapped[int] = mapped_column(default=0)

    # Campus map positioning
    map_x: Mapped[int] = mapped_column(default=0)
    map_y: Mapped[int] = mapped_column(default=0)
    map_width: Mapped[int] = mapped_column(default=120)
    map_height: Mapped[int] = mapped_column(default=90)
    accent_color: Mapped[str] = mapped_column(String(20), default="#3b82f6")

    spots: Mapped[list["ParkingSpot"]] = relationship("ParkingSpot", back_populates="zone", cascade="all, delete-orphan")


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    spot_code: Mapped[str] = mapped_column(String(30), primary_key=True, index=True)  # e.g. F4W-01
    zone_id: Mapped[int] = mapped_column(ForeignKey("parking_zones.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE", nullable=False, index=True)  # AVAILABLE, OCCUPIED
    current_occupant_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    current_vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    occupied_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Grid / visual layout coordinates
    row_num: Mapped[int] = mapped_column(default=1)
    col_num: Mapped[int] = mapped_column(default=1)
    is_ev: Mapped[bool] = mapped_column(default=False)
    is_accessible: Mapped[bool] = mapped_column(default=False)
    distance_to_gate: Mapped[int] = mapped_column(default=10)

    zone: Mapped["ParkingZone"] = relationship("ParkingZone", back_populates="spots")
    current_occupant: Mapped["User | None"] = relationship("User", foreign_keys=[current_occupant_id])
    current_vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", foreign_keys=[current_vehicle_id])


class OccupancyLog(Base):
    __tablename__ = "occupancy_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    spot_code: Mapped[str] = mapped_column(String(30), ForeignKey("parking_spots.spot_code"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False, index=True)
    check_in_time: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    check_out_time: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="occupancy_logs")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="occupancy_logs")
