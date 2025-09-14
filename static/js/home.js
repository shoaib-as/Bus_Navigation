// Initialize map (default center: Delhi)
var map = L.map('map').setView([28.6139, 77.2090], 12);

// ✅ OSM France tiles
L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, Tiles © OSM France',
    maxZoom: 20
}).addTo(map);

// Example bus marker
var busMarker = L.marker([28.6139, 77.2090]).addTo(map)
  .bindPopup("Bus Example")
  .openPopup();
