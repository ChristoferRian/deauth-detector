#!/usr/bin/env python3
import subprocess
import threading
import logging
import select

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeauthDetector:
    _process = None
    _is_running = False
    _thread = None
    # _interface = "wlx00c0cab4e516"
    _interface = "wlx00c0cab4e516"
    # Callback untuk mengirim pesan ke websocket (akan di-set dari API)
    send_callback = None

    @staticmethod
    def set_interface(interface):
        DeauthDetector._interface = interface

    @staticmethod
    def start():
        if DeauthDetector._is_running:
            return {"status": "running"}
        
        cmd = [
            "sudo", "tcpdump",
            "-l", "-i", DeauthDetector._interface,
            "type mgt subtype deauth"
        ]
        
        try:
            DeauthDetector._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            DeauthDetector._is_running = True
            DeauthDetector._thread = threading.Thread(target=DeauthDetector._monitor_output, daemon=True)
            DeauthDetector._thread.start()
            logger.info(f"Service mulai berjalan, menggunakan interface: {DeauthDetector._interface}")
            return {"status": "started"}
        except Exception as e:
            logger.error(f"Error saat memulai service: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _monitor_output():
        stdout = DeauthDetector._process.stdout
        try:
            # Loop dengan select, sehingga tidak _blocking_ selamanya
            while DeauthDetector._is_running:
                if stdout is None:
                    break
                ready, _, _ = select.select([stdout], [], [], 1)
                if ready:
                    line = stdout.readline()
                    if line:
                        message = f"Paket deauth terdeteksi: {line.strip()}"
                        # Jika callback tersedia, kirim pesan melalui websocket
                        if DeauthDetector.send_callback:
                            try:
                                DeauthDetector.send_callback(message)
                            except Exception as e:
                                logger.error(f"Error mengirim pesan via callback: {e}")
                        else:
                            print(message)
                    else:
                        break
                else:
                    continue
        except Exception as e:
            logger.error(f"Error monitoring: {e}")
        finally:
            DeauthDetector._is_running = False
            logger.info("Monitoring thread berhenti.")

    @staticmethod
    def stop():
        if DeauthDetector._process and DeauthDetector._is_running:
            DeauthDetector._is_running = False

            try:
                DeauthDetector._process.terminate()
                try:
                    DeauthDetector._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Timeout saat terminate, mencoba kill()")
                    DeauthDetector._process.kill()
                    DeauthDetector._process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating process: {e}")

            # Tutup stream agar thread _monitor_output_ tidak terblokir
            try:
                if DeauthDetector._process.stdout:
                    DeauthDetector._process.stdout.close()
            except Exception as e:
                logger.error(f"Error closing stdout: {e}")
            try:
                if DeauthDetector._process.stderr:
                    DeauthDetector._process.stderr.close()
            except Exception as e:
                logger.error(f"Error closing stderr: {e}")

            if DeauthDetector._thread is not None:
                DeauthDetector._thread.join(timeout=5)
                if DeauthDetector._thread.is_alive():
                    logger.warning("Thread monitoring masih aktif meski sudah mencoba join.")
            
            logger.info(f"Service berhenti!, interface: {DeauthDetector._interface} Free")
            DeauthDetector._process = None
            DeauthDetector._thread = None
            return {"status": "stopped"}
        else:
            logger.info("Service tidak berjalan.")
            return {"status": "not running"}
