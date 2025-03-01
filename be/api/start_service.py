from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import asyncio
import logging
from service.deauth_detector import DeauthDetector

router = APIRouter(tags=["Deauth Detection"])
logger = logging.getLogger(__name__)

# Kelas untuk mengelola koneksi WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket terkoneksi: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket terputus: {websocket.client}")

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        logger.info(f"Broadcast pesan: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error mengirim pesan ke {connection.client}: {e}")

manager = ConnectionManager()

# Endpoint WebSocket untuk menerima pesan secara realtime dari server
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Jika diperlukan, bisa juga menerima pesan dari client
            _ = await websocket.receive_text()
            # Di sini misalnya kita abaikan pesan masuk
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# HTTP endpoint untuk memulai deteksi
@router.post("/start", summary="Mulai deteksi paket deauth")
async def start_detection():
    result = DeauthDetector.start()
    if result.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Unknown error")
        )
    return {"message": "Deteksi dimulai"}

# HTTP endpoint untuk menghentikan deteksi
@router.post("/stop", summary="Hentikan deteksi paket deauth")
async def stop_detection():
    result = DeauthDetector.stop()
    return {"message": result["status"]}

# Untuk mengirim pesan dari thread deteksi ke WebSocket, kita butuh event loop.
# Pastikan kita mendapatkan event loop yang aktif.
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

def send_ws_callback(message: str):
    """Callback yang akan mengirim pesan ke semua client WebSocket."""
    if manager.active_connections:
        # Jalankan broadcast di event loop utama secara thread-safe
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), loop)
    else:
        logger.info("Tidak ada koneksi websocket aktif untuk mengirim pesan.")

# Set callback ini agar dipanggil oleh DeauthDetector saat ada pesan baru
DeauthDetector.send_callback = send_ws_callback
