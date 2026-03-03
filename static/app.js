(function () {
  const queryEl = document.getElementById('query');
  const submitBtn = document.getElementById('submit');
  const errorEl = document.getElementById('error');
  const waypointsEl = document.getElementById('waypoints');
  const waypointsList = document.getElementById('waypoints-list');
  const summaryEl = document.getElementById('summary');
  const summaryTime = document.getElementById('summary-time');
  const summaryDistance = document.getElementById('summary-distance');
  const overlayEl = document.getElementById('map-overlay');
  const overlayTime = document.getElementById('overlay-time');
  const overlayDistance = document.getElementById('overlay-distance');

  let map = null;
  let routeLayer = null;
  let markersLayer = null;

  function initMap() {
    if (map) return;
    map = L.map('map').setView([37.5, -122.2], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    routeLayer = L.layerGroup().addTo(map);
    markersLayer = L.layerGroup().addTo(map);
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.style.display = 'block';
    waypointsEl.style.display = 'none';
    summaryEl.style.display = 'none';
    overlayEl.style.display = 'none';
  }

  function hideError() {
    errorEl.style.display = 'none';
  }

  function formatDuration(minutes) {
    const m = Math.round(minutes);
    if (m < 60) return m + ' min';
    const h = Math.floor(m / 60);
    const rem = m % 60;
    return rem ? h + ' hr ' + rem + ' min' : h + ' hr';
  }

  function formatDistance(miles) {
    return miles.toFixed(1) + ' miles';
  }

  function renderResult(data) {
    hideError();
    waypointsList.innerHTML = '';
    data.waypoints.forEach(function (w) {
      const li = document.createElement('li');
      li.textContent = w.name;
      waypointsList.appendChild(li);
    });
    waypointsEl.style.display = 'block';

    const s = data.summary;
    const timeStr = formatDuration(s.duration_minutes);
    const distStr = formatDistance(s.distance_miles);
    summaryTime.textContent = timeStr;
    summaryDistance.textContent = distStr;
    summaryEl.style.display = 'block';

    overlayTime.textContent = timeStr;
    overlayDistance.textContent = distStr;
    overlayEl.style.display = 'block';

    routeLayer.clearLayers();
    markersLayer.clearLayers();

    if (!map) initMap();

    var latlngs = data.polyline.map(function (p) { return [p[1], p[0]]; });
    L.polyline(latlngs, { color: '#1a73e8', weight: 5 }).addTo(routeLayer);
    map.fitBounds(latlngs, { padding: [40, 40] });

    data.waypoints.forEach(function (w, i) {
      var marker = L.circleMarker([w.lat, w.lng], {
        radius: 6,
        fillColor: i === data.waypoints.length - 1 ? '#ea4335' : '#1a73e8',
        color: '#fff',
        weight: 2,
        fillOpacity: 1,
      }).addTo(markersLayer);
    });
  }

  submitBtn.addEventListener('click', async function () {
    var query = queryEl.value.trim();
    if (!query) {
      showError('Please enter a route description.');
      return;
    }
    submitBtn.disabled = true;
    hideError();
    try {
      var res = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
      });
      var data = await res.json().catch(function () { return null; });
      if (!res.ok) {
        showError(data && data.detail ? data.detail : 'Request failed.');
        return;
      }
      renderResult(data);
    } catch (e) {
      showError('Network error: ' + (e.message || 'Could not reach server.'));
    } finally {
      submitBtn.disabled = false;
    }
  });

  queryEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') submitBtn.click();
  });

  initMap();
})();
