/**
 * Campus Overview Map Renderer (Interactive SVG)
 */
export const CampusMap = {
  container: null,
  zonesData: [],
  buildingsData: [],
  onSelectZone: null,

  init(containerElement, onSelectZoneCallback) {
    this.container = containerElement;
    this.onSelectZone = onSelectZoneCallback;
  },

  render(campusData) {
    if (!this.container) return;
    this.zonesData = campusData.zones;
    this.buildingsData = campusData.buildings;

    const svgWidth = 1000;
    const svgHeight = 680;

    let svgHtml = `
      <svg id="campus-svg" viewBox="0 0 ${svgWidth} ${svgHeight}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <!-- Gradients -->
          <linearGradient id="ground-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0b132b" />
            <stop offset="100%" stop-color="#0f172a" />
          </linearGradient>

          <pattern id="road-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.03)" stroke-width="1"/>
          </pattern>

          <!-- Zone drop shadows -->
          <filter id="zone-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <!-- Campus Ground -->
        <rect width="${svgWidth}" height="${svgHeight}" fill="url(#ground-grad)" rx="16" />
        <rect width="${svgWidth}" height="${svgHeight}" fill="url(#road-grid)" rx="16" />

        <!-- Road Network & Walkways -->
        <g class="campus-roads">
          <!-- Main Ring Road -->
          <rect x="70" y="50" width="860" height="570" rx="30" fill="none" stroke="#1e293b" stroke-width="32" />
          <rect x="70" y="50" width="860" height="570" rx="30" fill="none" stroke="rgba(255, 255, 255, 0.25)" stroke-width="2" stroke-dasharray="14 12" />

          <!-- Center Avenue Cross -->
          <line x1="500" y1="50" x2="500" y2="620" stroke="#1e293b" stroke-width="28" />
          <line x1="500" y1="50" x2="500" y2="620" stroke="rgba(255, 255, 255, 0.25)" stroke-width="2" stroke-dasharray="12 10" />

          <line x1="70" y1="340" x2="930" y2="340" stroke="#1e293b" stroke-width="28" />
          <line x1="70" y1="340" x2="930" y2="340" stroke="rgba(255, 255, 255, 0.25)" stroke-width="2" stroke-dasharray="12 10" />

          <!-- Campus Center Courtyard -->
          <circle cx="500" cy="340" r="48" fill="#13233b" stroke="#38bdf8" stroke-width="3" stroke-opacity="0.4" />
          <circle cx="500" cy="340" r="28" fill="#0369a1" fill-opacity="0.2" />
          <text x="500" y="344" text-anchor="middle" fill="#94a3b8" font-size="11" font-weight="700" letter-spacing="1">CENTRAL QUAD</text>
        </g>

        <!-- Campus Landmarks & Academic Buildings -->
        <g class="campus-buildings">
          ${this.renderBuildings()}
        </g>

        <!-- Campus Parking Zones (Interactive) -->
        <g class="campus-zones">
          ${this.renderZones()}
        </g>

        <!-- Campus Gate Labels -->
        <g class="campus-gates" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#94a3b8">
          <text x="500" y="36" text-anchor="middle">↑ NORTH GATE (SERVICE & FACULTY)</text>
          <text x="500" y="660" text-anchor="middle">↓ SOUTH GATE & TRANSIT HUB</text>
          <text x="32" y="344" text-anchor="middle" transform="rotate(-90, 32, 344)">WEST ACCESS</text>
          <text x="968" y="344" text-anchor="middle" transform="rotate(90, 968, 344)">EAST GATE (TECH)</text>
        </g>
      </svg>
    `;

    this.container.innerHTML = svgHtml;
    this.attachEventListeners();
  },

  renderBuildings() {
    return this.buildingsData.map(b => {
      return `
        <g class="building-group" id="${b.id}">
          <!-- Building Base -->
          <rect x="${b.x}" y="${b.y}" width="${b.width}" height="${b.height}" rx="10" 
                fill="#111c33" stroke="rgba(255, 255, 255, 0.12)" stroke-width="1.5" />
          
          <!-- Inner architectural styling -->
          <rect x="${b.x + 8}" y="${b.y + 8}" width="${b.width - 16}" height="${b.height - 16}" rx="6" 
                fill="none" stroke="rgba(56, 189, 248, 0.15)" stroke-width="1" stroke-dasharray="4 4" />

          <!-- Building Label -->
          <text x="${b.x + b.width / 2}" y="${b.y + b.height / 2 - 2}" text-anchor="middle" 
                fill="#f1f5f9" font-size="12" font-weight="700" letter-spacing="0.5">
            ${b.label}
          </text>
          <text x="${b.x + b.width / 2}" y="${b.y + b.height / 2 + 16}" text-anchor="middle" 
                fill="#64748b" font-size="9.5" font-weight="500">
            ${b.name.length > 34 ? b.name.substring(0, 34) + '...' : b.name}
          </text>
        </g>
      `;
    }).join("");
  },

  renderZones() {
    return this.zonesData.map(z => {
      const isFull = z.available_spots === 0;
      const statusColor = isFull ? "#ef4444" : "#10b981";
      const vehicleIcon = z.allowed_vehicle_types.includes("TWO_WHEELER") && z.allowed_vehicle_types.includes("FOUR_WHEELER")
        ? "🚗 🛵"
        : z.allowed_vehicle_types.includes("FOUR_WHEELER") ? "🚗 4W" : "🛵 2W";

      return `
        <g class="campus-zone-group" data-zone-id="${z.id}" data-zone-code="${z.zone_code}">
          <!-- Zone Container Box -->
          <rect class="zone-bg" x="${z.map_x}" y="${z.map_y}" width="${z.map_width}" height="${z.map_height}" rx="12" 
                fill="#0f172a" fill-opacity="0.92" stroke="${z.accent_color}" stroke-width="2" />

          <!-- Zone Accent Header Banner -->
          <rect x="${z.map_x}" y="${z.map_y}" width="${z.map_width}" height="28" rx="12" 
                fill="${z.accent_color}" fill-opacity="0.18" />

          <!-- Zone Title -->
          <text x="${z.map_x + 12}" y="${z.map_y + 19}" fill="${z.accent_color}" 
                font-size="12" font-weight="800" letter-spacing="0.5">
            ${z.zone_code}
          </text>

          <!-- Vehicle Type Tag -->
          <text x="${z.map_x + z.map_width - 12}" y="${z.map_y + 19}" text-anchor="end" 
                fill="#94a3b8" font-size="10.5" font-weight="600">
            ${vehicleIcon}
          </text>

          <!-- Zone Name -->
          <text x="${z.map_x + 12}" y="${z.map_y + 46}" fill="#f8fafc" 
                font-size="11" font-weight="600">
            ${z.zone_name.length > 25 ? z.zone_name.substring(0, 24) + '…' : z.zone_name}
          </text>

          <!-- Allowed Roles Badge -->
          <text x="${z.map_x + 12}" y="${z.map_y + 64}" fill="#64748b" font-size="9.5" font-weight="500">
            Access: ${z.allowed_roles.replace(',', ' & ')}
          </text>

          <!-- Capacity Bar Background -->
          <rect x="${z.map_x + 12}" y="${z.map_y + 82}" width="${z.map_width - 24}" height="8" rx="4" 
                fill="rgba(255, 255, 255, 0.1)" />

          <!-- Capacity Bar Fill -->
          <rect x="${z.map_x + 12}" y="${z.map_y + 82}" 
                width="${Math.max(4, ((z.map_width - 24) * z.occupancy_rate) / 100)}" height="8" rx="4" 
                fill="${statusColor}" />

          <!-- Availability Counter Pill -->
          <g transform="translate(${z.map_x + 12}, ${z.map_y + 100})">
            <circle cx="5" cy="5" r="4" fill="${statusColor}" />
            <text x="14" y="9" fill="#e2e8f0" font-size="11" font-weight="700">
              ${z.available_spots} / ${z.total_spots} Available
            </text>
            <text x="${z.map_width - 24}" y="9" text-anchor="end" fill="#94a3b8" font-size="10.5" font-weight="600">
              ${z.occupancy_rate}%
            </text>
          </g>

          <!-- Drilldown Hint Icon -->
          <text x="${z.map_x + z.map_width - 14}" y="${z.map_y + 122}" text-anchor="end" 
                fill="${z.accent_color}" font-size="9.5" font-weight="600">
            Click to View Grid →
          </text>
        </g>
      `;
    }).join("");
  },

  attachEventListeners() {
    const zoneElements = this.container.querySelectorAll(".campus-zone-group");
    zoneElements.forEach(elem => {
      elem.addEventListener("click", () => {
        const zoneId = parseInt(elem.getAttribute("data-zone-id"), 10);
        if (this.onSelectZone) {
          this.onSelectZone(zoneId);
        }
      });
    });
  },

  highlightZone(zoneCode) {
    const allZones = this.container.querySelectorAll(".campus-zone-group");
    allZones.forEach(elem => {
      const code = elem.getAttribute("data-zone-code");
      const bg = elem.querySelector(".zone-bg");
      if (code === zoneCode) {
        bg.setAttribute("stroke", "#f59e0b");
        bg.setAttribute("stroke-width", "4");
        elem.classList.add("recommended-pulse");
      } else {
        bg.setAttribute("stroke-width", "2");
        elem.classList.remove("recommended-pulse");
      }
    });
  }
};
