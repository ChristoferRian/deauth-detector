import os
from dotenv import load_dotenv

load_dotenv

# _interface = str(os.getenv("INTERFACE"))
_interface = os.getenv("INTERFACE")

print("Interface yang digunakan: ",_interface)
print("tipe nilai interface nya: ",type(_interface))