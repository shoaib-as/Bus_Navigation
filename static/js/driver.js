let trackingInterval = null; // store the interval ID

function toggleTracking() {
    const busId = document.getElementById("bus").value;
    const trackButton = document.getElementById("trackButton");

    if (trackingInterval) {
        // Stop tracking
        clearInterval(trackingInterval);
        trackingInterval = null;
        trackButton.textContent = "Start Tracking";
        trackButton.disabled = false;
        alert("Live tracking stopped for your bus!");
    } else {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser");
            return;
        }

        // Start tracking
        trackButton.textContent = "Stop Tracking";
        trackButton.disabled = false; // allow stopping
        trackingInterval = setInterval(() => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;

                    fetch('/api/update-location/', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ bus_id: busId, latitude, longitude })
                    })
                    .then(res => res.json())
                    .then(data => console.log(data))
                    .catch(err => console.error(err));
                },
                (error) => {
                    console.error("Error getting location:", error);
                }
            );
        }, 5000);

        alert("Live tracking started for your bus!");
    }
}
