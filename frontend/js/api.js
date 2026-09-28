/**
 * API Service for College Campus Parking Management Platform
 */
const API_BASE = window.location.origin;

export const ParkingAPI = {
  async getCampusOverview() {
    const res = await fetch(`${API_BASE}/api/campus/overview`);
    if (!res.ok) throw new Error("Failed to load campus overview");
    return await res.json();
  },

  async getZoneDetail(zoneId, userRole = "PUBLIC") {
    const res = await fetch(`${API_BASE}/api/parking/zone/${zoneId}`, {
      headers: {
        "x-role": userRole
      }
    });
    if (!res.ok) throw new Error("Failed to load zone detail");
    return await res.json();
  },

  async suggestSpot(userId, vehicleId) {
    const res = await fetch(`${API_BASE}/api/parking/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, vehicle_id: vehicleId })
    });
    return await res.json();
  },

  async checkIn(spotCode, userId, vehicleId) {
    const res = await fetch(`${API_BASE}/api/parking/check-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        spot_code: spotCode,
        user_id: userId,
        vehicle_id: vehicleId
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Check-in failed");
    }
    return await res.json();
  },

  async checkOut(spotCode) {
    const res = await fetch(`${API_BASE}/api/parking/check-out`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spot_code: spotCode })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Check-out failed");
    }
    return await res.json();
  },

  async registerUser(userData) {
    const res = await fetch(`${API_BASE}/api/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }
    return await res.json();
  },

  async registerVisitor(visitorData) {
    const res = await fetch(`${API_BASE}/api/visitors/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(visitorData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Visitor registration failed");
    }
    return await res.json();
  },

  async getUsers() {
    const res = await fetch(`${API_BASE}/api/users`);
    if (!res.ok) throw new Error("Failed to fetch users");
    return await res.json();
  },

  async getLogs(role = "SECURITY", limit = 50) {
    const res = await fetch(`${API_BASE}/api/logs?limit=${limit}`, {
      headers: { "x-role": role }
    });
    if (!res.ok) throw new Error("Failed to fetch logs");
    return await res.json();
  },

  async triggerSimulationEvent() {
    const res = await fetch(`${API_BASE}/api/simulation/random-event`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Simulation event failed");
    return await res.json();
  },

  async resetSimulation() {
    const res = await fetch(`${API_BASE}/api/simulation/reset`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Reset failed");
    return await res.json();
  }
};
