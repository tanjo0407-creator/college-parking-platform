/**
 * QR Code Generator & Mobile Scan Simulator for Parking Spots
 */
export const QrModal = {
  renderQrSvg(text) {
    // Generate deterministic 21x21 QR code matrix visual for demo
    const size = 21;
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = (hash << 5) - hash + text.charCodeAt(i);
      hash |= 0;
    }

    let rects = "";
    // Standard corner markers
    const isCornerMarker = (r, c) => {
      if ((r < 7 && c < 7) || (r < 7 && c >= size - 7) || (r >= size - 7 && c < 7)) {
        if (r === 0 || r === 6 || c === 0 || c === 6 || (r >= size - 7 && (r === size - 7 || r === size - 1)) || (c >= size - 7 && (c === size - 7 || c === size - 1))) return true;
        if ((r >= 2 && r <= 4 && c >= 2 && c <= 4) || (r >= 2 && r <= 4 && c >= size - 5 && c <= size - 3) || (r >= size - 5 && r <= size - 3 && c >= 2 && c <= 4)) return true;
        return false;
      }
      return false;
    };

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const isCorner = isCornerMarker(r, c);
        const bit = ((hash ^ (r * 31 + c * 17)) & (1 << ((r + c) % 8))) !== 0;
        if (isCorner || (bit && !((r < 7 && c < 7) || (r < 7 && c >= size - 7) || (r >= size - 7 && c < 7)))) {
          rects += `<rect x="${c * 8}" y="${r * 8}" width="7.5" height="7.5" fill="#0f172a" />`;
        }
      }
    }

    return `
      <svg width="170" height="170" viewBox="0 0 ${size * 8} ${size * 8}" xmlns="http://www.w3.org/2000/svg">
        <rect width="${size * 8}" height="${size * 8}" fill="#ffffff" rx="8" />
        ${rects}
      </svg>
    `;
  },

  show(spot, zone, onScanSuccess) {
    const modal = document.getElementById("qr-modal");
    if (!modal) return;

    const qrContainer = document.getElementById("qr-svg-wrapper");
    const title = document.getElementById("qr-spot-title");
    const subtitle = document.getElementById("qr-spot-desc");
    const scanBtn = document.getElementById("qr-simulate-scan-btn");

    title.innerText = `Spot QR: ${spot.spot_code}`;
    subtitle.innerText = `${zone.zone_name} • Scan on arrival to auto-lock`;

    qrContainer.innerHTML = this.renderQrSvg(`https://parking.college.edu/check-in?spot=${spot.spot_code}`);

    scanBtn.onclick = () => {
      modal.style.display = "none";
      if (onScanSuccess) onScanSuccess(spot);
    };

    modal.style.display = "flex";
  }
};
