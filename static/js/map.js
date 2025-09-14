let map;
let markers = {};

async function initMap(buses) {
    const { Map, Marker, InfoWindow } = await google.maps.importLibrary("maps");

    map = new Map(document.getElementById("map"), {
        center: { lat: 28.61, lng: 77.23 }, // Default center
        zoom: 12,
    });

    buses.forEach(bus => {
        const marker = new Marker({
            position: { lat: parseFloat(bus.latitude), lng: parseFloat(bus.longitude) },
            map: map,
            title: bus.bus_number
        });

        const infoWindow = new InfoWindow({
            content: `<strong>Bus Number:</strong> ${bus.bus_number}`
        });

        marker.addListener("click", () => infoWindow.open(map, marker));

        markers[bus.bus_number] = marker;
    });

    setInterval(updateBusLocations, 5000);
}

function updateBusLocations() {
    Object.keys(markers).forEach(busNumber => {
        fetch(`/api/location/${busNumber}/`)
          .then(response => response.json())
          .then(data => {
              const marker = markers[busNumber];
              marker.setPosition({ lat: parseFloat(data.latitude), lng: parseFloat(data.longitude) });
          })
          .catch(err => console.error("Error updating location:", err));
    });
}
