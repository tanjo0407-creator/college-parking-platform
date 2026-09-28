import { ParkingAPI } from "./api.js";

/**
 * Traffic Simulator Manager & Activity Feed Logger
 */
export const SimulationManager = {
  intervalId: null,
  isRunning: false,
  activityListEl: null,

  init(activityContainerId) {
    this.activityListEl = document.getElementById(activityContainerId);
  },

  logActivity(text, type = "info") {
    if (!this.activityListEl) return;
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const item = document.createElement("div");
    item.className = `activity-item ${type}`;

    let icon = "⚡";
    if (type === "occupied") icon = "🚗";
    if (type === "vacated") icon = "🟢";

    item.innerHTML = `
      <span>${icon}</span>
      <div style="flex: 1;">${text}</div>
      <span class="activity-time">${timeStr}</span>
    `;

    this.activityListEl.prepend(item);

    // Keep max 25 items
    while (this.activityListEl.children.length > 25) {
      this.activityListEl.removeChild(this.activityListEl.lastChild);
    }
  },

  async triggerRandomEvent() {
    try {
      const res = await ParkingAPI.triggerSimulationEvent();
      if (res.action === "CHECK_IN") {
        this.logActivity(`Spot <strong>${res.spot_code}</strong> occupied by <strong>${res.user}</strong> (${res.vehicle_plate})`, "occupied");
      } else if (res.action === "CHECK_OUT") {
        this.logActivity(`Spot <strong>${res.spot_code}</strong> vacated in ${res.zone_code}`, "vacated");
      }
      return res;
    } catch (e) {
      console.error("Simulation event error:", e);
    }
  },

  toggleAutoSimulation(callbackOnTick) {
    if (this.isRunning) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      this.isRunning = false;
      this.logActivity("Traffic simulator paused.", "info");
      return false;
    } else {
      this.isRunning = true;
      this.logActivity("Traffic simulator started. Simulating live arrivals & departures.", "info");
      this.intervalId = setInterval(async () => {
        await this.triggerRandomEvent();
        if (callbackOnTick) callbackOnTick();
      }, 2400);
      return true;
    }
  },

  async resetAll(callbackOnReset) {
    try {
      await ParkingAPI.resetSimulation();
      this.logActivity("All campus parking spots reset to VACANT.", "vacated");
      if (callbackOnReset) callbackOnReset();
    } catch (e) {
      console.error("Reset error:", e);
    }
  }
};
