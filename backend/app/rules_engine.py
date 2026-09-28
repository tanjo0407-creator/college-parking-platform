
from sqlalchemy.orm import Session

from . import models


class AccessRuleResult:
    def __init__(self, allowed: bool, rule_code: str, message: str, eligible_zone_codes: list[str]):
        self.allowed = allowed
        self.rule_code = rule_code
        self.message = message
        self.eligible_zone_codes = eligible_zone_codes


def evaluate_campus_access_rules(user: models.User, vehicle: models.Vehicle) -> AccessRuleResult:
    """
    Evaluates campus access policy:
    1. Faculty / Admin + 4-Wheeler: Allowed in FACULTY_4W and VISITOR_PARKING.
    2. Faculty / Admin + 2-Wheeler: Allowed in FACULTY_2W and VISITOR_PARKING.
    3. Student + 2-Wheeler: Allowed in STUDENT_2W.
    4. Student + 4-Wheeler: Campus parking denied (rule violation alert).
    5. Visitor / Guest: Allowed in VISITOR_PARKING (2W or 4W).
    """
    role = user.role.upper()
    vtype = vehicle.vehicle_type.upper()

    # Rule 4: Student + 4-Wheeler DENIAL
    if role == "STUDENT" and vtype == "FOUR_WHEELER":
        return AccessRuleResult(
            allowed=False,
            rule_code="STUDENT_4W_DENIED",
            message="Rule Violation: Campus policy strictly prohibits student four-wheelers from parking on college grounds. Please use off-campus municipal parking.",
            eligible_zone_codes=[]
        )

    # Rule 3: Student + 2-Wheeler
    if role == "STUDENT" and vtype == "TWO_WHEELER":
        return AccessRuleResult(
            allowed=True,
            rule_code="SUCCESS",
            message="Access Granted: Authorized for Student Two-Wheeler Zone (STUDENT_2W).",
            eligible_zone_codes=["STUDENT_2W"]
        )

    # Rule 1: Faculty / Admin + 4-Wheeler
    if role in ["FACULTY", "ADMIN"] and vtype == "FOUR_WHEELER":
        return AccessRuleResult(
            allowed=True,
            rule_code="SUCCESS",
            message=f"Access Granted: Authorized for {role.capitalize()} Four-Wheeler Zone (FACULTY_4W) and Visitor Overflow.",
            eligible_zone_codes=["FACULTY_4W", "VISITOR_PARKING"]
        )

    # Rule 2: Faculty / Admin + 2-Wheeler
    if role in ["FACULTY", "ADMIN"] and vtype == "TWO_WHEELER":
        return AccessRuleResult(
            allowed=True,
            rule_code="SUCCESS",
            message=f"Access Granted: Authorized for {role.capitalize()} Two-Wheeler Zone (FACULTY_2W) and Visitor Overflow.",
            eligible_zone_codes=["FACULTY_2W", "VISITOR_PARKING"]
        )

    # Rule 5: Visitor / Guest (both 2W and 4W)
    if role == "VISITOR":
        return AccessRuleResult(
            allowed=True,
            rule_code="SUCCESS",
            message=f"Access Granted: Visitor authorized for Visitor Parking Zone (VISITOR_PARKING) for {vtype.replace('_', ' ').lower()}.",
            eligible_zone_codes=["VISITOR_PARKING"]
        )

    # Fallback default restriction
    return AccessRuleResult(
        allowed=False,
        rule_code="ACCESS_RESTRICTED",
        message=f"Access Denied: No parking zone matches role '{user.role}' with vehicle type '{vehicle.vehicle_type}'.",
        eligible_zone_codes=[]
    )


def find_best_spot_for_driver(
    db: Session,
    user: models.User,
    vehicle: models.Vehicle
) -> tuple[AccessRuleResult, models.ParkingSpot | None, models.ParkingZone | None]:
    """
    Runs the optimal parking allocation algorithm:
    1. Check rule compliance.
    2. Search eligible zones in priority order.
    3. Within eligible zone, choose available spot with lowest distance_to_gate score.
    """
    rule_eval = evaluate_campus_access_rules(user, vehicle)
    if not rule_eval.allowed:
        return rule_eval, None, None

    # Search eligible zones in priority order
    for zone_code in rule_eval.eligible_zone_codes:
        zone = db.query(models.ParkingZone).filter(models.ParkingZone.zone_code == zone_code).first()
        if not zone:
            continue

        # Look for available spots in this zone, sorted by distance_to_gate then spot_code
        available_spots = (
            db.query(models.ParkingSpot)
            .filter(
                models.ParkingSpot.zone_id == zone.id,
                models.ParkingSpot.status == "AVAILABLE"
            )
            .order_by(
                models.ParkingSpot.distance_to_gate.asc(),
                models.ParkingSpot.row_num.asc(),
                models.ParkingSpot.col_num.asc(),
                models.ParkingSpot.spot_code.asc()
            )
            .all()
        )

        if available_spots:
            best_spot = available_spots[0]
            rule_eval.message = f"Spot {best_spot.spot_code} in {zone.zone_name} is recommended as optimal."
            return rule_eval, best_spot, zone

    # If all eligible zones are full:
    rule_eval.allowed = False
    rule_eval.rule_code = "NO_SPOTS_AVAILABLE"
    rule_eval.message = f"All authorized parking zones ({', '.join(rule_eval.eligible_zone_codes)}) are currently at 100% capacity."
    return rule_eval, None, None
