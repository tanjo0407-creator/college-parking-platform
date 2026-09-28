import { ParkingAPI } from "./api.js";
import { CampusMap } from "./campusMap.js";
import { ZoneMap } from "./zoneMap.js";
import { SimulationManager } from "./simulation.js";
import { QrModal } from "./qrModal.js";

// Global App State
const AppState = {
  currentView: "campus", // "campus", "zone", or "logs"
  currentZoneId: null,
  currentZoneData: null,
  campusData: null,
  users: [],
  currentUser: null,
  currentVehicle: null,
  recommendedSpotCode: null,
  isSecurityMode: false,
  ws: null
};

// DOM Elements
const elements = {
  metricsTotal: document.getElementById("metric-total-spots"),
  metricsAvailable: document.getElementById("metric-available-spots"),
  metricsOccupied: document.getElementById("metric-occupied-spots"),
  metricsRate: document.getElementById("metric-occupancy-rate"),
  metricBarFill: document.getElementById("metric-bar-fill"),

  viewportTitle: document.getElementById("viewport-title"),
  backToCampusBtn: document.getElementById("back-to-campus-btn"),
  campusMapContainer: document.getElementById("campus-map-view"),
  zoneGridView: document.getElementById("zone-grid-view"),
  auditSection: document.getElementById("audit-section"),

  userSelect: document.getElementById("user-select"),
  userRoleBadge: document.getElementById("user-role-badge"),
  userVehicleLabel: document.getElementById("user-vehicle-label"),
  suggestSpotBtn: document.getElementById("suggest-spot-btn"),
  registerVisitorBtn: document.getElementById("register-visitor-btn"),

  securityToggle: document.getElementById("security-mode-toggle"),
  securityStatusText: document.getElementById("security-status-text"),
  viewLogsBtn: document.getElementById("view-logs-btn"),
  themeToggleBtn: document.getElementById("theme-toggle-btn"),

  simAutoBtn: document.getElementById("sim-auto-btn"),
  simStepBtn: document.getElementById("sim-step-btn"),
  simResetBtn: document.getElementById("sim-reset-btn"),

  // Modals
  spotModal: document.getElementById("spot-modal"),
  spotModalClose: document.getElementById("spot-modal-close"),
  spotModalTitle: document.getElementById("spot-modal-title"),
  spotModalBody: document.getElementById("spot-modal-body"),
  spotModalFooter: document.getElementById("spot-modal-footer"),

  visitorModal: document.getElementById("visitor-modal"),
  visitorModalClose: document.getElementById("visitor-modal-close"),
  visitorForm: document.getElementById("visitor-form"),

  violationModal: document.getElementById("violation-modal"),
  violationModalClose: document.getElementById("violation-modal-close"),
  violationTitle: document.getElementById("violation-title"),
  violationMsg: document.getElementById("violation-msg"),

  qrModalClose: document.getElementById("qr-modal-close")
};

// WebSocket Real-Time Connection
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  AppState.ws = new WebSocket(wsUrl);

  AppState.ws.onopen = () => {
    console.log("🟢 Real-time WebSocket connected to Campus Parking Server");
  };

  AppState.ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (e) {
      console.warn("WS Parse Error:", e);
    }
  };

  AppState.ws.onclose = () => {
    console.log("WebSocket closed, attempting reconnect in 3s...");
    setTimeout(initWebSocket, 3000);
  };
}

function handleWebSocketMessage(msg) {
  // Update live metrics and UI automatically
  if (msg.event === "SPOT_OCCUPIED") {
    if (AppState.currentView === "zone" && AppState.currentZoneId === msg.zone_id) {
      ZoneMap.updateSingleSpot(msg.spot_code, "OCCUPIED", msg.occupied_at);
    }
    refreshCampusOverview(false);
  } else if (msg.event === "SPOT_VACATED") {
    if (AppState.currentView === "zone" && AppState.currentZoneId === msg.zone_id) {
      ZoneMap.updateSingleSpot(msg.spot_code, "AVAILABLE", null);
    }
    refreshCampusOverview(false);
  } else if (msg.event === "CAMPUS_RESET") {
    refreshCampusOverview(true);
    if (AppState.currentView === "zone") {
      drilldownToZone(AppState.currentZoneId);
    }
  }
}

// Data Fetching & UI Updaters
async function refreshCampusOverview(renderMap = true) {
  try {
    const data = await ParkingAPI.getCampusOverview();
    AppState.campusData = data;

    // Update Top Metrics Bar
    elements.metricsTotal.innerText = data.metrics.total_spots;
    elements.metricsAvailable.innerText = data.metrics.available_spots;
    elements.metricsOccupied.innerText = data.metrics.occupied_spots;
    elements.metricsRate.innerText = `${data.metrics.overall_occupancy_rate}%`;
    elements.metricBarFill.style.width = `${data.metrics.overall_occupancy_rate}%`;

    if (data.metrics.overall_occupancy_rate > 85) {
      elements.metricBarFill.style.background = "var(--spot-red)";
    } else if (data.metrics.overall_occupancy_rate > 60) {
      elements.metricBarFill.style.background = "var(--spot-yellow)";
    } else {
      elements.metricBarFill.style.background = "var(--spot-green)";
    }

    if (renderMap && AppState.currentView === "campus") {
      CampusMap.render(data);
    }
  } catch (err) {
    console.error("Error refreshing campus overview:", err);
  }
}

async function loadUsers() {
  try {
    const users = await ParkingAPI.getUsers();
    AppState.users = users;
    renderUserSelectDropdown(users);
  } catch (err) {
    console.error("Error loading users:", err);
  }
}

function renderUserSelectDropdown(users) {
  elements.userSelect.innerHTML = "";
  users.forEach(u => {
    const v = u.vehicles[0];
    const vStr = v ? `${v.vehicle_type === 'FOUR_WHEELER' ? '🚗 4W' : '🛵 2W'} [${v.license_plate}]` : 'No vehicle';
    const opt = document.createElement("option");
    opt.value = u.id;
    opt.innerText = `${u.name} (${u.role}) • ${vStr}`;
    elements.userSelect.appendChild(opt);
  });

  if (users.length > 0) {
    selectUser(users[0].id);
  }
}

function selectUser(userId) {
  const user = AppState.users.find(u => u.id === parseInt(userId, 10));
  if (!user) return;

  AppState.currentUser = user;
  AppState.currentVehicle = user.vehicles[0] || null;

  // Update User Badge in UI
  elements.userRoleBadge.className = `role-badge role-${user.role.toLowerCase()}`;
  elements.userRoleBadge.innerText = user.role;

  if (AppState.currentVehicle) {
    elements.userVehicleLabel.innerText = `${AppState.currentVehicle.license_plate} (${AppState.currentVehicle.vehicle_type.replace('_', ' ')})`;
  } else {
    elements.userVehicleLabel.innerText = "No vehicle assigned";
  }
}

// Navigation & Drilldown Handlers
async function drilldownToZone(zoneId, highlightSpot = null) {
  AppState.currentView = "zone";
  AppState.currentZoneId = zoneId;
  AppState.recommendedSpotCode = highlightSpot;

  elements.campusMapContainer.style.display = "none";
  elements.auditSection.style.display = "none";
  elements.zoneGridView.style.display = "flex";
  elements.backToCampusBtn.style.display = "inline-flex";

  try {
    const userRole = AppState.isSecurityMode ? "SECURITY" : "PUBLIC";
    const zoneData = await ParkingAPI.getZoneDetail(zoneId, userRole);
    AppState.currentZoneData = zoneData;

    elements.viewportTitle.innerText = `${zoneData.zone_name} (${zoneData.zone_code})`;
    ZoneMap.render(zoneData, highlightSpot);
  } catch (err) {
    console.error("Failed to load zone detail:", err);
  }
}

function returnToCampusOverview() {
  AppState.currentView = "campus";
  AppState.currentZoneId = null;
  AppState.currentZoneData = null;
  AppState.recommendedSpotCode = null;

  elements.zoneGridView.style.display = "none";
  elements.auditSection.style.display = "none";
  elements.campusMapContainer.style.display = "flex";
  elements.backToCampusBtn.style.display = "none";
  elements.viewportTitle.innerText = "College Campus Overview Map";

  refreshCampusOverview(true);
}

// Smart Spot Allocation Workflow
async function handleSuggestSpot() {
  if (!AppState.currentUser || !AppState.currentVehicle) {
    alert("Please select a profile with a registered vehicle first.");
    return;
  }

  try {
    const res = await ParkingAPI.suggestSpot(AppState.currentUser.id, AppState.currentVehicle.id);

    // Check for rule violation (e.g. Student + 4W denial)
    if (!res.allowed) {
      if (res.rule_code === "STUDENT_4W_DENIED") {
        showViolationModal(
          "Student 4-Wheeler Parking Denied",
          res.message,
          "Campus Environmental & Safety Regulation: Undergrad and graduate student four-wheelers are strictly restricted from university parking zones to ensure adequate emergency lane clearances and faculty access."
        );
      } else {
        showViolationModal("Allocation Failed", res.message, `Code: ${res.rule_code}`);
      }
      return;
    }

    // Allocation Succeeded
    const bestSpot = res.best_spot;
    const targetZone = res.target_zone;

    SimulationManager.logActivity(
      `Allocated optimal spot <strong>${bestSpot.spot_code}</strong> in <strong>${targetZone.zone_code}</strong> for ${AppState.currentUser.name}`,
      "info"
    );

    // Highlight zone on campus map and automatically drill down
    CampusMap.highlightZone(targetZone.zone_code);

    setTimeout(() => {
      drilldownToZone(targetZone.id, bestSpot.spot_code);
    }, 450);
  } catch (err) {
    console.error("Suggest spot error:", err);
    alert("Failed to find optimal spot: " + err.message);
  }
}

// Spot Modal & Check-In/Check-Out Operations
function handleSpotClick(spot, zone) {
  const isOccupied = (spot.status === "OCCUPIED");
  const isSecurity = AppState.isSecurityMode;

  elements.spotModalTitle.innerText = `Spot ${spot.spot_code} • ${zone.zone_name}`;

  let bodyHtml = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
      <span style="font-size: 0.85rem; color: #94a3b8;">Current Status</span>
      <span style="font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.78rem; background: ${isOccupied ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}; color: ${isOccupied ? '#f87171' : '#34d399'};">
        ${isOccupied ? 'OCCUPIED' : 'VACANT / AVAILABLE'}
      </span>
    </div>

    <div class="detail-row">
      <span class="detail-label">Zone / Section</span>
      <span class="detail-val">${zone.zone_code} (${zone.location_label})</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Allowed Roles</span>
      <span class="detail-val">${zone.allowed_roles.replace(',', ', ')}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Allowed Vehicle Types</span>
      <span class="detail-val">${zone.allowed_vehicle_types.replace('_', ' ')}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Features</span>
      <span class="detail-val">${spot.is_ev ? '⚡ EV Charging ' : ''}${spot.is_accessible ? '♿ Accessible' : ''}${!spot.is_ev && !spot.is_accessible ? 'Standard Bay' : ''}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Proximity to Gate</span>
      <span class="detail-val">${spot.distance_to_gate}m (Walking: ~${Math.round(spot.distance_to_gate * 0.8)}s)</span>
    </div>
  `;

  if (isOccupied) {
    bodyHtml += `
      <div style="margin-top: 1.25rem; padding: 0.85rem; background: rgba(0, 0, 0, 0.3); border-radius: 8px; border: 1px solid var(--bg-card-border);">
        <h4 style="font-size: 0.85rem; color: ${isSecurity ? '#38bdf8' : '#94a3b8'}; margin-bottom: 0.5rem; display: flex; justify-content: space-between;">
          <span>${isSecurity ? '🔒 Secured Occupant Records (Enforcement View)' : '🛡️ Public View (Identity Masked)'}</span>
          ${!isSecurity ? '<span style="font-size: 0.72rem; color: #64748b;">Toggle Security Mode for full details</span>' : ''}
        </h4>
        <div class="detail-row">
          <span class="detail-label">Driver Name</span>
          <span class="detail-val">${spot.occupant ? spot.occupant.name : 'Occupied'}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Role & Dept</span>
          <span class="detail-val">${spot.occupant ? `${spot.occupant.role} • ${spot.occupant.department_or_purpose}` : 'N/A'}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">License Plate</span>
          <span class="detail-val" style="font-family: monospace; font-size: 0.95rem;">${spot.occupant ? spot.occupant.license_plate : '••••-•••'}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Occupied Since</span>
          <span class="detail-val">${spot.occupied_at ? new Date(spot.occupied_at).toLocaleTimeString() : 'Active'}</span>
        </div>
      </div>
    `;
  }

  elements.spotModalBody.innerHTML = bodyHtml;

  // Footer Buttons
  let footerHtml = `
    <button class="btn btn-secondary" id="modal-qr-btn">Show QR Code</button>
  `;

  if (!isOccupied) {
    footerHtml += `
      <button class="btn btn-outline-green" id="modal-checkin-btn">
        <span>🚗</span> Mark as Occupied / Check-In
      </button>
    `;
  } else {
    footerHtml += `
      <button class="btn btn-danger" id="modal-checkout-btn">
        <span>🏁</span> Vacate / Check-Out
      </button>
    `;
  }

  elements.spotModalFooter.innerHTML = footerHtml;

  // Button actions
  document.getElementById("modal-qr-btn").onclick = () => {
    elements.spotModal.style.display = "none";
    QrModal.show(spot, zone, async (scannedSpot) => {
      await performCheckIn(scannedSpot.spot_code);
    });
  };

  const checkinBtn = document.getElementById("modal-checkin-btn");
  if (checkinBtn) {
    checkinBtn.onclick = async () => {
      await performCheckIn(spot.spot_code);
      elements.spotModal.style.display = "none";
    };
  }

  const checkoutBtn = document.getElementById("modal-checkout-btn");
  if (checkoutBtn) {
    checkoutBtn.onclick = async () => {
      await performCheckOut(spot.spot_code);
      elements.spotModal.style.display = "none";
    };
  }

  elements.spotModal.style.display = "flex";
}

async function performCheckIn(spotCode) {
  if (!AppState.currentUser || !AppState.currentVehicle) {
    alert("Please select a driver profile to check in.");
    return;
  }

  try {
    const res = await ParkingAPI.checkIn(spotCode, AppState.currentUser.id, AppState.currentVehicle.id);
    SimulationManager.logActivity(
      `Check-In confirmed: <strong>${AppState.currentUser.name}</strong> parked at <strong>${spotCode}</strong>`,
      "occupied"
    );
    // Refresh zone immediately
    if (AppState.currentZoneId) {
      drilldownToZone(AppState.currentZoneId);
    }
  } catch (err) {
    showViolationModal("Check-In Denied", err.message, "Please review campus parking regulations or select an authorized zone.");
  }
}

async function performCheckOut(spotCode) {
  try {
    const res = await ParkingAPI.checkOut(spotCode);
    SimulationManager.logActivity(
      `Spot <strong>${spotCode}</strong> vacated (Duration: ${res.duration_minutes || 0}m)`,
      "vacated"
    );
    // Refresh zone
    if (AppState.currentZoneId) {
      drilldownToZone(AppState.currentZoneId);
    }
  } catch (err) {
    alert("Check-out failed: " + err.message);
  }
}

// Rule Violation Alert Modal
function showViolationModal(title, message, policyNote) {
  elements.violationTitle.innerText = title;
  elements.violationMsg.innerText = message;
  document.getElementById("violation-policy-note").innerText = policyNote;
  elements.violationModal.style.display = "flex";
}

// User & Vehicle Registration Modal
function openVisitorModal() {
  elements.visitorModal.style.display = "flex";
}

async function handleVisitorSubmit(e) {
  e.preventDefault();
  const role = document.getElementById("vis-role").value;
  const vehicleType = document.getElementById("vis-vtype").value;
  const name = document.getElementById("vis-name").value.trim();
  const phone = document.getElementById("vis-phone").value.trim();
  const plate = document.getElementById("vis-plate").value.trim();
  const purpose = document.getElementById("vis-purpose").value.trim();

  try {
    const res = await ParkingAPI.registerUser({
      name,
      phone,
      role,
      department_or_purpose: purpose,
      license_plate: plate,
      vehicle_type: vehicleType
    });

    elements.visitorModal.style.display = "none";
    elements.visitorForm.reset();

    // Reload users and select the newly registered user
    await loadUsers();
    selectUser(res.user.id);

    SimulationManager.logActivity(
      `New user <strong>${name}</strong> (${role}) registered vehicle <strong>${plate}</strong>`,
      "info"
    );

    // Check access rule evaluation
    if (!res.rule_evaluation.allowed) {
      if (res.rule_evaluation.rule_code === "STUDENT_4W_DENIED") {
        showViolationModal(
          "Student 4-Wheeler Parking Denied",
          res.rule_evaluation.message,
          "Campus Environmental & Safety Regulation: Undergrad and graduate student four-wheelers are strictly restricted from university parking zones to ensure adequate emergency lane clearances and faculty access."
        );
      } else {
        showViolationModal("Access Denied", res.rule_evaluation.message, `Rule Code: ${res.rule_evaluation.rule_code}`);
      }
      return;
    }

    // If allowed, drilldown to target zone and highlight suggested spot
    if (res.target_zone) {
      const targetZoneObj = AppState.campusData.zones.find(z => z.zone_code === res.target_zone.zone_code);
      if (targetZoneObj) {
        CampusMap.highlightZone(targetZoneObj.zone_code);
        setTimeout(() => {
          drilldownToZone(targetZoneObj.id, res.suggested_spot);
        }, 350);
      }
    }
  } catch (err) {
    alert("Registration failed: " + err.message);
  }
}

// Security / Audit Log View
async function toggleLogsView() {
  if (AppState.currentView === "logs") {
    returnToCampusOverview();
    elements.viewLogsBtn.innerText = "📋 Enforcement Logs";
  } else {
    AppState.currentView = "logs";
    elements.campusMapContainer.style.display = "none";
    elements.zoneGridView.style.display = "none";
    elements.backToCampusBtn.style.display = "inline-flex";
    elements.auditSection.style.display = "block";
    elements.viewportTitle.innerText = "Campus Security & Enforcement Audit Records";
    elements.viewLogsBtn.innerText = "🗺️ Back to Map";

    await renderAuditLogsTable();
  }
}

async function renderAuditLogsTable() {
  const tbody = document.getElementById("audit-table-body");
  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem;">Loading logs...</td></tr>`;

  try {
    const logs = await ParkingAPI.getLogs(AppState.isSecurityMode ? "SECURITY" : "PUBLIC", 50);
    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem;">No occupancy logs recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const isStillParked = !l.check_out_time;
      const statusBadge = isStillParked
        ? `<span style="background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">ACTIVE</span>`
        : `<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.72rem;">COMPLETED</span>`;

      return `
        <tr>
          <td><strong style="color: #38bdf8;">${l.spot_code}</strong></td>
          <td>${statusBadge}</td>
          <td>${AppState.isSecurityMode ? l.user_name : 'Protected Driver'} <span class="role-badge role-${l.user_role.toLowerCase()}">${l.user_role}</span></td>
          <td>${AppState.isSecurityMode ? l.user_department : 'Campus Affiliate'}</td>
          <td style="font-family: monospace;">${AppState.isSecurityMode ? l.license_plate : '••••-•••'} (${l.vehicle_type.replace('_', ' ')})</td>
          <td>${new Date(l.check_in_time).toLocaleTimeString()}</td>
          <td>${l.duration_minutes ? `${l.duration_minutes} min` : 'Ongoing'}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #ef4444; padding: 2rem;">Error loading logs: ${err.message}</td></tr>`;
  }
}

// Security Mode Toggle Handler
function toggleSecurityMode() {
  AppState.isSecurityMode = !AppState.isSecurityMode;
  elements.securityToggle.classList.toggle("active", AppState.isSecurityMode);
  elements.securityStatusText.innerText = AppState.isSecurityMode ? "Enforcement Mode (RBAC Auth)" : "Public View";

  if (AppState.currentView === "zone" && AppState.currentZoneId) {
    drilldownToZone(AppState.currentZoneId, AppState.recommendedSpotCode);
  } else if (AppState.currentView === "logs") {
    renderAuditLogsTable();
  }
}

// Theme Switcher
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
  const nextTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", nextTheme);
  elements.themeToggleBtn.innerText = nextTheme === "dark" ? "🌙" : "☀️";
}

// Event Listeners Setup
function setupEventListeners() {
  // Navigation
  elements.backToCampusBtn.onclick = returnToCampusOverview;
  elements.viewLogsBtn.onclick = toggleLogsView;
  elements.securityToggle.onclick = toggleSecurityMode;
  elements.themeToggleBtn.onclick = toggleTheme;

  // Profile Selection & Spot Suggestion
  elements.userSelect.onchange = (e) => selectUser(e.target.value);
  elements.suggestSpotBtn.onclick = handleSuggestSpot;
  elements.registerVisitorBtn.onclick = openVisitorModal;

  // Simulation Controls
  elements.simAutoBtn.onclick = () => {
    const isRunning = SimulationManager.toggleAutoSimulation(() => {
      // Callback on tick: refresh zone view if open
      if (AppState.currentView === "zone" && AppState.currentZoneId) {
        drilldownToZone(AppState.currentZoneId);
      }
    });
    elements.simAutoBtn.innerText = isRunning ? "⏸ Pause Simulator" : "▶ Start Traffic Simulator";
    elements.simAutoBtn.className = isRunning ? "btn btn-danger" : "btn btn-primary";
  };

  elements.simStepBtn.onclick = async () => {
    await SimulationManager.triggerRandomEvent();
    if (AppState.currentView === "zone" && AppState.currentZoneId) {
      drilldownToZone(AppState.currentZoneId);
    }
  };

  elements.simResetBtn.onclick = async () => {
    if (confirm("Reset all campus parking spots to vacant?")) {
      await SimulationManager.resetAll(() => {
        refreshCampusOverview(true);
        if (AppState.currentView === "zone" && AppState.currentZoneId) {
          drilldownToZone(AppState.currentZoneId);
        }
      });
    }
  };

  // Modals Close Handlers
  elements.spotModalClose.onclick = () => elements.spotModal.style.display = "none";
  elements.visitorModalClose.onclick = () => elements.visitorModal.style.display = "none";
  elements.violationModalClose.onclick = () => elements.violationModal.style.display = "none";
  elements.qrModalClose.onclick = () => document.getElementById("qr-modal").style.display = "none";

  // Light dismiss on clicking outside modal
  window.onclick = (e) => {
    if (e.target.classList.contains("modal-overlay")) {
      e.target.style.display = "none";
    }
  };

  // Visitor Form Submit
  elements.visitorForm.onsubmit = handleVisitorSubmit;
}

// Initial Boot
async function initApp() {
  CampusMap.init(elements.campusMapContainer, (zoneId) => {
    drilldownToZone(zoneId);
  });

  ZoneMap.init(elements.zoneGridView, (spot, zone) => {
    handleSpotClick(spot, zone);
  });

  SimulationManager.init("activity-list");

  setupEventListeners();
  initWebSocket();

  await loadUsers();
  await refreshCampusOverview(true);

  SimulationManager.logActivity("Campus Parking Management Platform initialized.", "info");
}

document.addEventListener("DOMContentLoaded", initApp);
