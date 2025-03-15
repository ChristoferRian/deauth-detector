document.addEventListener("DOMContentLoaded", function () {
    // Tentukan URL backend secara eksplisit karena FastAPI berjalan di port 8000
    // const backendUrl = "http://localhost:8000";
     // Initialize status checking
    
      
    const currentHost = window.location.hostname;
    
    // Use the current hostname for both HTTP and WebSocket connections
    const backendUrl = `http://${currentHost}:8000`;
    console.log(backendUrl);
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://${currentHost}:8000/ws`;
    
    let socket;
    // Function to connect to WebSocket


        // Fungsi untuk mengecek status mode monitor
    function checkMonitorStatus() {
      fetch(`${backendUrl}/check-status`)
        .then(response => {
          if (!response.ok) {
            throw new Error("Gagal mengecek status monitor.");
          }
          return response.json();
        })
        .then(data => {
          console.log("Status response:", data);
          updateToggleStatus(data.status);
        })
        .catch(error => {
          console.error("Error checking status:", error);
          updateToggleStatus("error");
        });
    }

    // Fungsi untuk memperbarui status toggle
    function updateToggleStatus(status) {
      const toggle = document.getElementById("monitor-status-toggle");
      const statusText = document.getElementById("status-text");
      
      if (status === "running") {
        toggle.checked = true;
        toggle.classList.remove("bg-danger");
        toggle.classList.add("bg-success");
        statusText.textContent = "Running";
        statusText.classList.remove("text-danger");
        statusText.classList.add("text-success");
      } else if (status === "idle") {
        toggle.checked = false;
        toggle.classList.remove("bg-success");
        toggle.classList.add("bg-danger");
        statusText.textContent = "Idle";
        statusText.classList.remove("text-success");
        statusText.classList.add("text-danger");
      } else {
        toggle.checked = false;
        statusText.textContent = "Error";
        statusText.classList.add("text-danger");
      }
    }

    // Panggil fungsi cek status setiap 5 detik
    function startStatusPolling() {
      // Cek status saat halaman dimuat
      checkMonitorStatus();
      
      // Set interval untuk pengecekan status secara berkala
      setInterval(checkMonitorStatus, 5000);
    }

    // Panggil polling saat halaman dimuat
    startStatusPolling();

    function connectWebSocket() {
      socket = new WebSocket(wsUrl);
  
      socket.onopen = function () {
        console.log("WebSocket connection established.");
        addStatusMessage("WebSocket terhubung", "success");
      };
  
      socket.onmessage = function (event) {
        const message = event.data;
        console.log("Message received:", message);
        addDeauthMessage(message);
      };
  
      socket.onerror = function (error) {
        console.error("WebSocket error:", error);
        addStatusMessage("WebSocket error", "danger");
      };
  
      socket.onclose = function (event) {
        console.log("WebSocket connection closed.", event);
        addStatusMessage("WebSocket terputus. Mencoba menghubungkan kembali...", "warning");
        // Try to reconnect every 3 seconds if disconnected
        setTimeout(connectWebSocket, 3000);
      };
    }
  
    // Call the connection function when the page has loaded
    connectWebSocket();
  
    // Event listener for Start Detection button
    const startBtn = document.getElementById("start-btn");
    startBtn.addEventListener("click", function () {
      fetch(`${backendUrl}/start`, {
        method: "POST",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Gagal memulai deteksi.");
          }
          return response.json();
        })
        .then((data) => {
          console.log("Start response:", data);
          // Optional: Show notification that detection has started
          addStatusMessage("Deteksi dimulai.", "success");
          checkMonitorStatus(); // Perbarui status setelah memulai deteksi
        })
        .catch((error) => {
          console.error("Error:", error);
          addStatusMessage("Error: " + error.message, "danger");
        });
    });
  
    // Event listener for Stop Detection button
    const stopBtn = document.getElementById("stop-btn");
    stopBtn.addEventListener("click", function () {
      fetch(`${backendUrl}/stop`, {
        method: "POST",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Gagal menghentikan deteksi.");
          }
          return response.json();
        })
        .then((data) => {
          console.log("Stop response:", data);
          // Optional: Show notification that detection has stopped
          addStatusMessage("Deteksi dihentikan.", "warning");
          checkMonitorStatus(); // Perbarui status setelah menghentikan deteksi
        })
        .catch((error) => {
          console.error("Error:", error);
          addStatusMessage("Error: " + error.message, "danger");
        });
    });
  
    // Function to add detection message to the list
    function addDeauthMessage(message) {
      const deauthList = document.getElementById("deauth-list");
  
      // Create list item element with Bootstrap styling
      const li = document.createElement("li");
      li.className = "list-group-item deauth-item";
  
      // Element for text message
      const messageSpan = document.createElement("span");
      messageSpan.textContent = message + " ";
  
      // Badge element to display the time the message was received
      const badge = document.createElement("span");
      badge.className = "badge bg-secondary";
      badge.textContent = new Date().toLocaleTimeString();
  
      li.appendChild(messageSpan);
      li.appendChild(badge);
  
      // Add list item to ul
      deauthList.appendChild(li);
    }
  
    // Function to add status message (e.g., start/stop notifications)
    function addStatusMessage(message, type) {
      // Create Bootstrap alert element
      const alertDiv = document.createElement("div");
      alertDiv.className = `alert alert-${type} mt-2`;
      alertDiv.textContent = message;
  
      // Place alert above the card (e.g., inside the main container)
      const mainContainer = document.querySelector("main .container");
      mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
  
      // Remove alert after 5 seconds
      setTimeout(() => {
        alertDiv.remove();
      }, 5000);
    }
});