from datetime import datetime
from pydantic import BaseModel, ConfigDict


# Vehicle Schemas
class VehicleBase(BaseModel):
    license_plate: str
    vehicle_type: str  # TWO_WHEELER, FOUR_WHEELER


class VehicleCreate(VehicleBase):
    user_id: int


class VehicleOut(VehicleBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# User Schemas
class UserBase(BaseModel):
    name: str
    phone: str
    role: str  # FACULTY, ADMIN, STUDENT, VISITOR
    department_or_purpose: str


class UserCreate(UserBase):
    pass


class UserOut(UserBase):
    id: int
    vehicles: list[VehicleOut] = []

    model_config = ConfigDict(from_attributes=True)


# User Registration Schema (Any Role: FACULTY, ADMIN, STUDENT, VISITOR)
class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    role: str  # FACULTY, ADMIN, STUDENT, VISITOR
    department_or_purpose: str
    license_plate: str
    vehicle_type: str  # TWO_WHEELER, FOUR_WHEELER


# Visitor Registration Schema
class VisitorRegisterRequest(BaseModel):
    name: str
    phone: str
    license_plate: str
    vehicle_type: str  # TWO_WHEELER, FOUR_WHEELER
    purpose: str = "Campus Guest"


# Spot Schemas
class ParkingSpotBase(BaseModel):
    spot_code: str
    zone_id: int
    status: str
    row_num: int
    col_num: int
    is_ev: bool = False
    is_accessible: bool = False
    distance_to_gate: int = 10


class OccupantDetail(BaseModel):
    user_id: int
    name: str
    role: str
    department_or_purpose: str
    license_plate: str
    vehicle_type: str
    occupied_at: datetime | None = None


class ParkingSpotOut(ParkingSpotBase):
    occupied_at: datetime | None = None
    # Public view has occupant details masked unless authorized
    occupant: OccupantDetail | None = None

    model_config = ConfigDict(from_attributes=True)


# Zone Schemas
class ParkingZoneBase(BaseModel):
    id: int
    zone_code: str
    zone_name: str
    allowed_roles: str
    allowed_vehicle_types: str
    description: str | None = None
    location_label: str | None = None
    total_spots: int
    map_x: int
    map_y: int
    map_width: int
    map_height: int
    accent_color: str


class ParkingZoneOverview(ParkingZoneBase):
    available_spots: int
    occupied_spots: int
    occupancy_rate: float


class ParkingZoneDetail(ParkingZoneBase):
    available_spots: int
    occupied_spots: int
    occupancy_rate: float
    spots: list[ParkingSpotOut] = []


# Campus Overview Schema
class CampusMetrics(BaseModel):
    total_spots: int
    available_spots: int
    occupied_spots: int
    overall_occupancy_rate: float


class CampusOverviewResponse(BaseModel):
    metrics: CampusMetrics
    zones: list[ParkingZoneOverview]
    buildings: list[dict]
    server_time: datetime


# Parking Action Schemas
class SpotSuggestRequest(BaseModel):
    user_id: int
    vehicle_id: int


class SpotSuggestResponse(BaseModel):
    allowed: bool
    message: str
    rule_code: str  # SUCCESS, STUDENT_4W_DENIED, NO_SPOTS_AVAILABLE, INVALID_VEHICLE
    best_spot: ParkingSpotOut | None = None
    target_zone: ParkingZoneOverview | None = None
    eligible_zones: list[str] = []


class CheckInRequest(BaseModel):
    spot_code: str
    user_id: int
    vehicle_id: int


class CheckInResponse(BaseModel):
    success: bool
    message: str
    spot_code: str
    check_in_time: datetime
    spot: ParkingSpotOut


class CheckOutRequest(BaseModel):
    spot_code: str


class CheckOutResponse(BaseModel):
    success: bool
    message: str
    spot_code: str
    vacated_at: datetime
    duration_minutes: int | None = None


# Occupancy Log Schema
class OccupancyLogOut(BaseModel):
    id: int
    spot_code: str
    user_id: int
    user_name: str
    user_role: str
    user_department: str
    license_plate: str
    vehicle_type: str
    check_in_time: datetime
    check_out_time: datetime | None = None
    duration_minutes: int | None = None

    model_config = ConfigDict(from_attributes=True)
