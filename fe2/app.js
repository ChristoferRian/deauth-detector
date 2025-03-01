document.addEventListener("DOMContentLoaded", function () {
    // Tentukan URL backend secara eksplisit karena FastAPI berjalan di port 8000
    const backendUrl = "http://localhost:8000";
      
    // Tentukan protokol untuk WebSocket (ws jika http, wss jika https)
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://localhost:8000/ws`;
    let socket;
  
    // Fungsi untuk menghubungkan ke WebSocket
    function connectWebSocket() {
      socket = new WebSocket(wsUrl);
  
      socket.onopen = function () {
        console.log("WebSocket connection established.");
      };
  
      socket.onmessage = function (event) {
        const message = event.data;
        console.log("Message received:", message);
        addDeauthMessage(message);
      };
  
      socket.onerror = function (error) {
        console.error("WebSocket error:", error);
      };
  
      socket.onclose = function (event) {
        console.log("WebSocket connection closed.", event);
        // Coba reconnect setiap 3 detik jika terputus
        setTimeout(connectWebSocket, 3000);
      };
    }
  
    // Panggil fungsi koneksi saat halaman telah termuat
    connectWebSocket();
  
    // Event listener untuk tombol Start Detection
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
          // Opsional: Tampilkan notifikasi bahwa deteksi telah dimulai
          addStatusMessage("Deteksi dimulai.", "success");
        })
        .catch((error) => {
          console.error("Error:", error);
          addStatusMessage("Error: " + error.message, "danger");
        });
    });
  
    // Event listener untuk tombol Stop Detection
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
          // Opsional: Tampilkan notifikasi bahwa deteksi telah dihentikan
          addStatusMessage("Deteksi dihentikan.", "warning");
        })
        .catch((error) => {
          console.error("Error:", error);
          addStatusMessage("Error: " + error.message, "danger");
        });
    });
  
    // Fungsi untuk menambahkan pesan deteksi ke daftar
    function addDeauthMessage(message) {
      const deauthList = document.getElementById("deauth-list");
  
      // Buat elemen list item dengan styling Bootstrap
      const li = document.createElement("li");
      li.className = "list-group-item deauth-item";
  
      // Elemen untuk pesan teks
      const messageSpan = document.createElement("span");
      messageSpan.textContent = message + " ";
  
      // Elemen badge untuk menampilkan waktu pesan diterima
      const badge = document.createElement("span");
      badge.className = "badge bg-secondary";
      badge.textContent = new Date().toLocaleTimeString();
  
      li.appendChild(messageSpan);
      li.appendChild(badge);
  
      // Tambahkan list item ke dalam ul
      deauthList.appendChild(li);
    }
  
    // Fungsi untuk menambahkan pesan status (misalnya notifikasi start/stop)
    function addStatusMessage(message, type) {
      // Buat elemen alert Bootstrap
      const alertDiv = document.createElement("div");
      alertDiv.className = `alert alert-${type} mt-2`;
      alertDiv.textContent = message;
  
      // Tempelkan alert di atas card (misalnya di dalam container utama)
      const mainContainer = document.querySelector("main .container");
      mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
  
      // Hapus alert setelah 5 detik
      setTimeout(() => {
        alertDiv.remove();
      }, 5000);
    }
  });
  