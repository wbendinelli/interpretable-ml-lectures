'use strict';
(() => {
  // Small, locally authored line symbols. Labels carry the meaning; these
  // outlines do not encode numerical results or replace accessible text.
  const paths = {
    source: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 5V3h8v2M8 10h8M8 14h8"/>',
    clean: '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
    cohort: '<circle cx="9" cy="7" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M19 20v-3a5 5 0 0 0-3-4"/>',
    fit: '<path d="M4 19V5M4 19h16M8 15l4-5 4 2 4-7"/>',
    choose: '<path d="M4 7h9M4 12h7M4 17h5M14 14l3 3 5-7"/>',
    explain: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M10 7v6M7 10h6"/>',
    model: '<rect x="5" y="5" width="14" height="14" rx="3"/><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4M9 9h6v6H9z"/>',
    shuffle: '<path d="M3 6h3c5 0 7 12 12 12h3M17 14l4 4-4 4M3 18h3c2 0 4-3 5-6M15 7c1-1 2-1 3-1h3M17 2l4 4-4 4"/>',
    repeat: '<path d="M20 8a8 8 0 0 0-14-3L3 8M3 3v5h5M4 16a8 8 0 0 0 14 3l3-3M21 21v-5h-5"/>',
    error: '<path d="M4 19V5M4 19h16M8 15v-3M12 15V8M16 15v-5"/>',
    fixed: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
    global: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18M12 3c-5 5-5 13 0 18"/>',
    context: '<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>',
    dependence: '<circle cx="5" cy="6" r="3"/><circle cx="19" cy="6" r="3"/><circle cx="12" cy="19" r="3"/><path d="M8 6h8M6.5 8.6l4 7.8M17.5 8.6l-4 7.8"/>',
    interpretation: '<path d="M3 12s3-6 9-6 9 6 9 6-3 6-9 6-9-6-9-6Z"/><circle cx="12" cy="12" r="3"/>',
    arrow: '<path d="M4 12h16M14 6l6 6-6 6"/>'
  };
  const icon = name => `<svg class="meaning-icon" viewBox="0 0 24 24"${name === 'arrow' ? ' preserveAspectRatio="none"' : ''} fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths[name] || paths.explain}</svg>`;

  function diagnosticSketch(key) {
    if (key === 'within') {
      return `<div class="diagnostic-sketch subgroup-sketch" role="img" aria-label="Heart disease moves only among records in the same diabetes category: Yes, No or Unknown."><span class="sketch-label">Diabetes groups</span>${['Yes', 'No', 'Unknown'].map(category => `<div class="subgroup-lane"><span class="subgroup-category">${category}</span><span class="sketch-chip">Heart</span><span class="subgroup-exchange" aria-hidden="true">↔</span><span class="sketch-chip">Heart</span></div>`).join('')}</div>`;
    }
    const joint = key === 'joint';
    const moving = joint ? ['Heart', 'Diabetes'] : [key === 'diabetes' ? 'Diabetes' : 'Heart'];
    const unit = `<span class="sketch-unit ${joint ? 'paired-unit' : ''}">${moving.map(label => `<span class="sketch-chip">${label}</span>`).join('')}</span>`;
    const meaning = joint ? 'Move heart disease and diabetes from the same donor row together into another record.' : `Move only ${key === 'diabetes' ? 'diabetes' : 'heart disease'} from the donor row into another record.`;
    return `<div class="diagnostic-sketch transfer-sketch" role="img" aria-label="${meaning}"><div class="sketch-record"><span class="sketch-label">Donor row</span>${unit}</div><span class="sketch-transfer" aria-hidden="true"><span class="transfer-dot"></span>${icon('arrow')}</span><div class="sketch-record sketch-destination"><span class="sketch-label">Another record</span>${unit}</div></div>`;
  }
  window.PFIVisualAids = { icon, diagnosticSketch };
})();
