import sqlite3
import subprocess
import datetime
import threading
import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List

app = FastAPI()

DATABASE = "deauth_packets.db"
INTERFACE = "wlan0"  # Ubah sesuai dengan interface yang digunakan

# Model untuk response data paket
class Packet(BaseModel):
    id: int
    timestamp: str
    interface: str
    packet_data: str

# Manajer koneksi WebSocket untuk mengelola klien yang tersambung
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                # Jika terjadi kesalahan pengiriman, lewati saja
                pass

manager = ConnectionManager()

# Endpoint WebSocket untuk mengirim data secara real time ke frontend
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Loop untuk menjaga koneksi tetap aktif; tidak perlu memproses pesan masuk
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Fungsi untuk membuat database dan tabel jika belum ada
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deauth_packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            interface TEXT,
            packet_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Fungsi untuk memasukkan data paket ke dalam database
def insert_packet(timestamp: str, interface: str, packet_data: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO deauth_packets (timestamp, interface, packet_data)
        VALUES (?, ?, ?)
    ''', (timestamp, interface, packet_data))
    conn.commit()
    conn.close()

# Variabel global untuk menyimpan event loop utama FastAPI
event_loop = None

# Fungsi untuk mendeteksi paket deauthentication menggunakan tcpdump
def detect_deauth(interface: str = INTERFACE):
    init_db()  # Pastikan database sudah ada

    cmd = ["sudo", "tcpdump", "-l", "-i", interface, "type mgt subtype deauth"]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception as e:
        print(f"Gagal menjalankan tcpdump: {e}")
        return

    print(f"Monitoring paket deauthentication pada interface {interface}...\n(CTRL+C untuk berhenti)")
    while True:
        line = process.stdout.readline()
        if line:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            packet_line = line.strip()
            print(f"Paket deauth terdeteksi [{timestamp}]: {packet_line}")
            # Simpan ke database
            insert_packet(timestamp, interface, packet_line)
            # Buat payload yang akan dikirim ke frontend
            packet_info = {
                "timestamp": timestamp,
                "interface": interface,
                "packet_data": packet_line
            }
            # Jika event_loop sudah tersimpan, gunakan untuk menjadwalkan broadcast ke WebSocket
            if event_loop is not None:
                # Menggunakan call_soon_threadsafe untuk memanggil coroutine broadcast
                event_loop.call_soon_threadsafe(
                    asyncio.create_task, manager.broadcast(json.dumps(packet_info))
                )
        else:
            break

# Endpoint untuk mengambil data paket dari database (opsional)
@app.get("/api/deauth_packets", response_model=List[Packet])
def get_packets():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, interface, packet_data FROM deauth_packets")
    rows = cursor.fetchall()
    conn.close()
    packets = []
    for row in rows:
        packets.append(Packet(id=row[0], timestamp=row[1], interface=row[2], packet_data=row[3]))
    return packets

# Endpoint untuk memulai deteksi secara manual (opsional)
@app.post("/api/start_detection")
def start_detection():
    thread = threading.Thread(target=detect_deauth, args=(INTERFACE,), daemon=True)
    thread.start()
    return {"message": "Deteksi paket deauthentication dimulai di background."}

# Pada startup, simpan event loop utama dan mulai thread deteksi
@app.on_event("startup")
async def startup_event():
    global event_loop
    event_loop = asyncio.get_running_loop()
    thread = threading.Thread(target=detect_deauth, args=(INTERFACE,), daemon=True)
    thread.start()
