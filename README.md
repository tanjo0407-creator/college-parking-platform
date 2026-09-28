# 🎓 CampusPark • College Campus Parking Management Platform

A modern, production-grade College Parking Management Platform featuring an interactive visual campus map, rule-based parking spot assignment, real-time spot status synchronization via WebSockets, and secure occupant record management with Role-Based Access Control (RBAC).

---

## 🏛️ System Architecture

### 1. Campus Parking Zones & Access Control Policy

| Zone Code | Zone Name | Allowed Roles | Vehicle Types | Campus Location |
|---|---|---|---|---|
| `FACULTY_4W` | Faculty & Admin 4-Wheeler Bay | `FACULTY`, `ADMIN` | `FOUR_WHEELER` | North Quad, adjacent to Administration Complex |
| `FACULTY_2W` | Faculty & Admin 2-Wheeler Shed | `FACULTY`, `ADMIN` | `TWO_WHEELER` | East Wing, near Science & Tech Complex |
| `STUDENT_2W` | Student 2-Wheeler Plaza | `STUDENT` | `TWO_WHEELER` | South Quad, near Central Library & Cafeteria |
| `VISITOR_PARKING` | Visitor & Guest Bay | `VISITOR`, `FACULTY`, `ADMIN` | `TWO_WHEELER`, `FOUR_WHEELER` | Main Gate & Reception Checkpoint |

#### Access Control Rules
1. **Faculty / Admin + 4-Wheeler**: Permitted in `FACULTY_4W` (primary) and `VISITOR_PARKING` (overflow).
2. **Faculty / Admin + 2-Wheeler**: Permitted in `FACULTY_2W` (primary) and `VISITOR_PARKING` (overflow).
3. **Student + 2-Wheeler**: Permitted in `STUDENT_2W`.
4. **Student + 4-Wheeler**: **Campus parking strictly denied.** Triggers a high-priority rule violation alert modal citing campus safety and environmental restrictions.
5. **Visitor / Guest**: Permitted in `VISITOR_PARKING` upon completing quick digital guest registration.

---

## 🏗️ Relational Database Schema

- **`User`**: `id`, `name`, `phone`, `role` (`FACULTY`, `ADMIN`, `STUDENT`, `VISITOR`), `department_or_purpose`
- **`Vehicle`**: `id`, `user_id`, `license_plate`, `vehicle_type` (`TWO_WHEELER`, `FOUR_WHEELER`)
- **`ParkingZone`**: `id`, `zone_code`, `zone_name`, `allowed_roles`, `allowed_vehicle_types`, `location_label`, `total_spots`, `map_x`, `map_y`, `accent_color`
- **`ParkingSpot`**: `spot_code`, `zone_id`, `status` (`AVAILABLE`, `OCCUPIED`, `RESERVED`), `current_occupant_id`, `current_vehicle_id`, `occupied_at`, `row_num`, `col_num`, `is_ev`, `is_accessible`, `distance_to_gate`
- **`OccupancyLog`**: `id`, `spot_code`, `user_id`, `vehicle_id`, `check_in_time`, `check_out_time`

---

## ⚡ Key API Endpoints

- `GET /api/campus/overview`: Returns campus metrics, building landmarks, and real-time occupancy counts per zone.
- `GET /api/parking/zone/{zone_id}`: Returns full spot matrix and status for a specific parking zone (masks occupant data unless in Security/Enforcement mode).
- `POST /api/parking/suggest`: Evaluates access control rules for `{ user_id, vehicle_id }` and returns the optimal spot code.
- `POST /api/parking/check-in`: Accepts `{ spot_code, user_id, vehicle_id }`, locks the spot, sets status to `OCCUPIED`, logs the event, and broadcasts a WebSocket notification.
- `POST /api/parking/check-out`: Accepts `{ spot_code }`, clears occupant details, restores status to `AVAILABLE`, closes the log, and broadcasts a WebSocket notification.
- `POST /api/visitors/register`: Fast registration creating user + vehicle records and auto-suggesting an optimal spot in `VISITOR_PARKING`.
- `GET /api/logs`: Returns secure occupancy enforcement logs with duration calculations.
- `POST /api/simulation/random-event`: Generates a simulated check-in or check-out event to test multi-client map synchronization.
- `POST /api/simulation/reset`: Resets all parking spots to vacant.
- `WebSocket /ws`: Real-time bidirectional connection for live broadcast of spot status changes.

---

## 🚀 Running the Platform Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
```
The application will start on **`http://127.0.0.1:8000`**.

### 3. Open in Browser
Visit **`http://127.0.0.1:8000`** in your browser.

---

## 🎨 UI/UX Features

- **Interactive Campus Overview Map**: High-level SVG map displaying campus landmarks (Admin Complex, STEM Labs, Central Library, Student Center, Main Gate) and interactive parking zone hubs with live capacity gauges.
- **2D Visual Spot Grid Layout**: Drill down into any zone to see individual numbered bays, driving lanes, EV charging indicators, and accessible handicap markings.
  - 🟢 **Green**: Vacant / Available
  - 🔴 **Red**: Occupied
  - 🟡 **Yellow**: Recommended / Suggested Optimal Spot
- **Smart Spot Recommendation**: 1-click allocation matching role, vehicle type, and shortest walk distance.
- **Live Check-In / Check-Out**: Instant visual state toggle synchronized across all clients via WebSockets.
- **Data Privacy & RBAC**: Public view masks occupant identity (`••••-•••`); Security Mode reveals full enforcement metadata.
- **Spot QR Code Generator & Mobile Scan Simulator**: View QR code for any spot and simulate driver arrival with phone camera scan.
- **Traffic Simulator**: Auto-traffic generator for stress testing real-time synchronization.
