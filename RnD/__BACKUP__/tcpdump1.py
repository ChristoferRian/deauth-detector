#!/usr/bin/env python3
import subprocess
import argparse

def detect_deauth(interface="wlan0"):
    """
    Fungsi ini menjalankan tcpdump untuk memonitor paket deauthentication.
    Filter yang digunakan adalah: 'type mgt subtype deauth'
    """
    # Menyiapkan perintah tcpdump dengan output yang tidak di-buffer (-l)
    cmd = ["sudo", "tcpdump", "-l", "-i", interface, "type mgt subtype deauth"]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except Exception as e:
        print(f"Gagal menjalankan tcpdump: {e}")
        return

    print(f"Monitoring paket deauthentication pada interface {interface}...\n(CTRL+C untuk berhenti)")
    try:
        while True:
            line = process.stdout.readline()
            if line:
                # Setiap baris output yang diterima dianggap sebagai paket deauth
                print(f"Paket deauth terdeteksi: {line.strip()}")
            else:
                break
    except KeyboardInterrupt:
        print("\nPenghentian deteksi...")
        process.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deteksi paket deauthentication menggunakan tcpdump")
    parser.add_argument("-i", "--interface", type=str, default="wlan0",
                        help="Interface yang digunakan (default: wlan0). Pastikan dalam mode monitor!")
    args = parser.parse_args()
    detect_deauth(args.interface)
