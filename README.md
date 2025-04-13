
# Deauth-Detector

Deauthentication Attacks Detector using TCPdump as the main enginge for detecting and capture deauthentication packets sent from unknown OUI (Organization Uniquie Identifier).

captured deauthentication packets will be sent to user in the website using websocket in real-time.


## Automatic Installation

```bash
wget https://raw.githubusercontent.com/ChristoferRian/deauth-detector/refs/heads/main/auto_deploy.sh
```
```bash
sudo chmod +x auto_deploy.sh
```
```bash
sudo ./auto_deploy.sh
```

## Manual Installation
### Clone this Repository
```bash
git clone https://github.com/ChristoferRian/deauth-detector.git
```    
### setup visudo
```bash
sudo visudo
```
add this at the end of line

    $ORIGINAL_USER ALL=(ALL) NOPASSWD: ALL
    www-data ALL=(ALL) NOPASSWD: ALL
change $ORIGINAL_USER to current user

### install dependency
```bash
sudo apt install git nginx network-manager python3-pip python3-venv python3-websockets websocketd -y
```
### setup venv for the backend
```bash
cd deauth-detector/be/
python3 -m venv venv
source venv/bin/activate
```

### install python3 requirements
```bash
pip install -r requirements.txt
```
### adding cronjob for backend
```bash
crontab -e
```
add this at the end of line

    @reboot sleep 15 && bash $ORIGINAL_USER_HOME/deauth-detector/be/run_services.sh
change $ORIGINAL_USER_HOME to path this Repository in your local

### copy fe folder to /var/www/
```bash
sudo cp -r deauth-detector/fe2 /var/www/
sudo chmod -R +777 /var/www/fe2
sudo chown -R www-data:www-data /var/www/fe2
```

### setup nginx for frontend
```bash
 sudo cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    root /var/www/fe2;

    index index.html index.htm index.nginx-debian.html;
    server_name _;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # WebSocket proxy configuration
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API call proxy configurations
    location /start {
        proxy_pass http://localhost:8000/start;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /stop {
        proxy_pass http://localhost:8000/stop;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Add a new location block to proxy all API requests
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

EOF
```
