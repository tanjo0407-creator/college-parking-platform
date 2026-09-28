/**
 * 2D Visual Parking Spot Grid Layout Renderer
 */
export const ZoneMap = {
  container: null,
  zoneData: null,
  recommendedSpotCode: null,
  onSpotClick: null,

  init(containerElement, onSpotClickCallback) {
    this.container = containerElement;
    this.onSpotClick = onSpotClickCallback;
  },

  render(zoneData, recommendedSpotCode = null) {
    if (!this.container) return;
    this.zoneData = zoneData;
    this.recommendedSpotCode = recommendedSpotCode;

    // Group spots into rows based on row_num
    const rowsMap = {};
    zoneData.spots.forEach(spot => {
      const r = spot.row_num || 1;
      if (!rowsMap[r]) rowsMap[r] = [];
      rowsMap[r].push(spot);
    });

    const sortedRows = Object.keys(rowsMap).sort((a, b) => parseInt(a) - parseInt(b));

    let html = `
      <div class="zone-grid-wrapper">
        <div class="zone-info-banner" style="border-left: 4px solid ${zoneData.accent_color}; background: rgba(15, 23, 42, 0.6); padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <h2 style="font-size: 1.25rem; font-weight: 800; color: ${zoneData.accent_color}; margin-bottom: 0.2rem;">
              ${zoneData.zone_name}
            </h2>
            <p style="font-size: 0.82rem; color: #94a3b8;">
              ${zoneData.location_label} • Permitted: <strong style="color: #f1f5f9;">${zoneData.allowed_roles.replace(',', ', ')}</strong> (${zoneData.allowed_vehicle_types.replace('_', ' ')})
            </p>
          </div>
          <div style="display: flex; gap: 0.75rem; align-items: center;">
            <div style="text-align: right;">
              <div style="font-size: 1.1rem; font-weight: 800; color: ${zoneData.available_spots > 0 ? '#10b981' : '#ef4444'};">
                ${zoneData.available_spots} / ${zoneData.total_spots}
              </div>
              <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase;">Available Spots</div>
            </div>
            <div style="width: 44px; height: 44px; border-radius: 50%; background: ${zoneData.available_spots > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'}; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem; color: ${zoneData.available_spots > 0 ? '#10b981' : '#ef4444'};">
              ${100 - zoneData.occupancy_rate}%
            </div>
          </div>
        </div>

        <div class="zone-grid-container">
    `;

    sortedRows.forEach((rowKey, idx) => {
      const spotsInRow = rowsMap[rowKey].sort((a, b) => (a.col_num || 0) - (b.col_num || 0));

      html += `<div class="parking-row" data-row="${rowKey}">`;
      spotsInRow.forEach(spot => {
        const isRecommended = (this.recommendedSpotCode && spot.spot_code === this.recommendedSpotCode);
        const isOccupied = (spot.status === "OCCUPIED");

        let statusClass = "spot-available";
        let statusBadge = "VACANT";
        let statusIcon = "🟢";
        let centerIcon = "🅿️";

        if (isOccupied) {
          statusClass = "spot-occupied";
          statusBadge = "OCCUPIED";
          statusIcon = "🔴";
          centerIcon = zoneData.allowed_vehicle_types.includes("TWO_WHEELER") && !zoneData.allowed_vehicle_types.includes("FOUR_WHEELER") ? "🏍️" : "🚗";
        }

        if (isRecommended && !isOccupied) {
          statusClass = "spot-recommended";
          statusBadge = "RECOMMENDED";
          statusIcon = "🟡";
        }

        html += `
          <div class="parking-spot-card ${statusClass}" 
               data-spot-code="${spot.spot_code}" 
               title="Click to view details or check in/out">
            <div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
              <span class="spot-code-label">${spot.spot_code}</span>
              <span style="font-size: 0.65rem;">${statusIcon}</span>
            </div>

            <div class="spot-vehicle-icon">
              ${centerIcon}
            </div>

            <div class="spot-tags">
              ${spot.is_ev ? '<span title="Electric Vehicle Charging" style="background: rgba(14, 165, 233, 0.2); color: #38bdf8; padding: 1px 4px; border-radius: 3px; font-weight: 700;">EV</span>' : ''}
              ${spot.is_accessible ? '<span title="Accessible Handicap Spot" style="background: rgba(168, 85, 247, 0.2); color: #c084fc; padding: 1px 4px; border-radius: 3px; font-weight: 700;">♿</span>' : ''}
            </div>

            <div style="font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">
              ${statusBadge}
            </div>
          </div>
        `;
      });
      html += `</div>`;

      // Insert central driving lane divider between upper and lower rows
      if (idx === Math.floor(sortedRows.length / 2) - 1) {
        html += `
          <div class="driving-lane">
            <span>◄◄ ONE WAY DRIVING LANE • SPEED LIMIT 10 MPH ►►</span>
          </div>
        `;
      }
    });

    html += `
        </div>
      </div>
    `;

    this.container.innerHTML = html;
    this.attachEventListeners();
  },

  attachEventListeners() {
    const spotCards = this.container.querySelectorAll(".parking-spot-card");
    spotCards.forEach(card => {
      card.addEventListener("click", () => {
        const spotCode = card.getAttribute("data-spot-code");
        const spotObj = this.zoneData.spots.find(s => s.spot_code === spotCode);
        if (this.onSpotClick && spotObj) {
          this.onSpotClick(spotObj, this.zoneData);
        }
      });
    });
  },

  updateSingleSpot(spotCode, newStatus, occupiedAt = null) {
    if (!this.zoneData) return;
    const spot = this.zoneData.spots.find(s => s.spot_code === spotCode);
    if (!spot) return;

    spot.status = newStatus;
    spot.occupied_at = occupiedAt;

    // Recount available/occupied
    const occupiedCount = this.zoneData.spots.filter(s => s.status === "OCCUPIED").length;
    this.zoneData.occupied_spots = occupiedCount;
    this.zoneData.available_spots = this.zoneData.total_spots - occupiedCount;
    this.zoneData.occupancy_rate = Math.round((occupiedCount / this.zoneData.total_spots) * 100);

    // Re-render
    this.render(this.zoneData, this.recommendedSpotCode);
  }
};
