/* global L */

const API_BASE_URL = 'http://localhost:5000';

const map = L.map('map').setView([12.9716, 77.5946], 15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

const boundaryLayer = L.geoJSON(null, {
  style: {
    color: '#2e8b57',
    weight: 2,
    fillColor: '#98fb98',
    fillOpacity: 0.3,
  },
}).addTo(map);

const coverageLayer = L.geoJSON(null, {
  style: feature => {
    if (feature.properties?.type === 'coverage_segment') {
      return {
        color: feature.properties.spray_on ? '#1f77b4' : '#ff7f0e',
        weight: feature.properties.spray_on ? 3 : 2,
        dashArray: feature.properties.spray_on ? null : '4 6',
      };
    }
    return { color: '#1f77b4', weight: 2 };
  },
  onEachFeature: (feature, layer) => {
    if (feature.properties?.type === 'coverage_segment') {
      const { order, spray_on, length } = feature.properties;
      layer.bindPopup(
        `Segment #${order}<br/>` +
          `Spray on: ${spray_on ? 'Yes' : 'No'}<br/>` +
          `Length: ${length.toFixed(6)}`
      );
    }
  },
}).addTo(map);

const trackLayer = L.layerGroup().addTo(map);

const boundaryInput = document.getElementById('boundary-input');
const holesInput = document.getElementById('holes-input');
const sprayWidthInput = document.getElementById('spray-width-input');
const angleResolutionInput = document.getElementById('angle-resolution-input');
const includeDeadheadInput = document.getElementById('include-deadhead-input');
const planSummary = document.getElementById('plan-summary');
const trackInput = document.getElementById('track-input');
const usePlanBoundaryCheckbox = document.getElementById('use-plan-boundary');
const trackSummary = document.getElementById('track-summary');

function showMessage(targetEl, message, isError = false) {
  targetEl.textContent = message;
  targetEl.classList.toggle('error', isError);
}

function parseJSONInput(value, fallback = null) {
  if (!value || !value.trim()) {
    return fallback;
  }
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error('Invalid JSON. Please check your input.');
  }
}

function fitToLayer(layer) {
  try {
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.2));
    }
  } catch (error) {
    // ignore
  }
}

function renderCoverage(geojson) {
  boundaryLayer.clearLayers();
  coverageLayer.clearLayers();

  const boundaryFeatures = geojson.features.filter(
    feature => feature.properties?.type === 'farm_boundary'
  );
  const coverageFeatures = geojson.features.filter(
    feature => feature.properties?.type === 'coverage_segment'
  );

  if (boundaryFeatures.length) {
    boundaryLayer.addData(boundaryFeatures);
  }
  if (coverageFeatures.length) {
    coverageLayer.addData(coverageFeatures);
  }

  fitToLayer(coverageLayer.getLayers().length ? coverageLayer : boundaryLayer);
}

async function planCoverage() {
  let boundary;
  let holes;
  try {
    boundary = parseJSONInput(boundaryInput.value);
    if (!boundary) throw new Error('Boundary is required.');
    holes = parseJSONInput(holesInput.value, []);
  } catch (error) {
    showMessage(planSummary, error.message, true);
    return;
  }

  const payload = {
    boundary,
    holes,
    spray_width: parseFloat(sprayWidthInput.value) || 0.0002,
    angle_resolution: parseFloat(angleResolutionInput.value) || 5,
    include_deadhead: includeDeadheadInput.checked,
  };

  showMessage(planSummary, 'Planning coverage...', false);

  try {
    const response = await fetch(`${API_BASE_URL}/plan-coverage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.error || `Request failed with ${response.status}`);
    }

    const data = await response.json();
    renderCoverage(data.geojson);
    const summaryLines = Object.entries(data.summary)
      .map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toFixed(6) : value}`)
      .join('\n');
    showMessage(planSummary, summaryLines);
  } catch (error) {
    showMessage(planSummary, error.message, true);
  }
}

async function analyseTrack() {
  let track;
  try {
    track = parseJSONInput(trackInput.value);
    if (!track || !Array.isArray(track) || track.length < 2) {
      throw new Error('Track must have at least two coordinates.');
    }
  } catch (error) {
    showMessage(trackSummary, error.message, true);
    return;
  }

  let boundary = null;
  let holes = null;
  if (usePlanBoundaryCheckbox.checked) {
    try {
      boundary = parseJSONInput(boundaryInput.value, null);
      holes = parseJSONInput(holesInput.value, null);
    } catch (error) {
      showMessage(trackSummary, `Unable to reuse boundary/holes: ${error.message}`, true);
      return;
    }
  }

  const payload = {
    track,
    spray_width: parseFloat(sprayWidthInput.value) || 0.0002,
  };

  if (boundary) payload.boundary = boundary;
  if (holes) payload.holes = holes;

  showMessage(trackSummary, 'Analysing track...', false);

  try {
    const response = await fetch(`${API_BASE_URL}/track-coverage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.error || `Request failed with ${response.status}`);
    }

    const data = await response.json();
    renderTrack(track, boundary);
    const lines = Object.entries(data)
      .map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toFixed(6) : value}`)
      .join('\n');
    showMessage(trackSummary, lines);
  } catch (error) {
    showMessage(trackSummary, error.message, true);
  }
}

function renderTrack(trackCoordinates, boundary) {
  trackLayer.clearLayers();

  const trackLine = L.polyline(trackCoordinates.map(([lon, lat]) => [lat, lon]), {
    color: '#ff1493',
    weight: 3,
  }).addTo(trackLayer);

  if (boundary) {
    const polygon = L.polygon(boundary.map(([lon, lat]) => [lat, lon]), {
      color: '#8b0000',
      weight: 1,
      fillOpacity: 0,
    }).addTo(trackLayer);
    fitToLayer(polygon);
  } else {
    fitToLayer(trackLine);
  }
}

function loadExample() {
  const exampleBoundary = [
    [77.5950, 12.9720],
    [77.5960, 12.9726],
    [77.5971, 12.9719],
    [77.5968, 12.9706],
    [77.5956, 12.9701],
    [77.5948, 12.9709],
  ];

  const exampleHoles = [
    [
      [77.5954, 12.9718],
      [77.5957, 12.9719],
      [77.5958, 12.9716],
      [77.5955, 12.9713],
      [77.5953, 12.9715],
    ],
  ];

  const exampleTrack = [
    [77.5950, 12.9720],
    [77.5958, 12.9721],
    [77.5965, 12.9718],
    [77.5962, 12.9709],
    [77.5954, 12.9706],
  ];

  boundaryInput.value = JSON.stringify(exampleBoundary, null, 2);
  holesInput.value = JSON.stringify(exampleHoles, null, 2);
  trackInput.value = JSON.stringify(exampleTrack, null, 2);
  sprayWidthInput.value = '0.0002';
  angleResolutionInput.value = '5';

  showMessage(planSummary, 'Example data loaded. Calculating coverage...');

  // Small delay to allow UI to refresh before triggering the request
  window.requestAnimationFrame(() => {
    planCoverage();
  });
}

document.getElementById('plan-btn').addEventListener('click', planCoverage);
document.getElementById('track-btn').addEventListener('click', analyseTrack);
document.getElementById('load-example-btn').addEventListener('click', loadExample);

// Load default example on first visit for convenience
loadExample();

