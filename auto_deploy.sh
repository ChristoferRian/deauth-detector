#!/bin/bash

function show_progress() {
    echo "===> $1"
}

# Fungsi untuk menampilkan pesan selesai
function show_done() {
    echo "===> SELESAI: $1"
    echo ""
}

ORIGINAL_USER=$(logname || echo $SUDO_USER || echo $USER)
ORIGINAL_USER_HOME=$(eval echo ~$ORIGINAL_USER)

install_dependency(){
    show_progress "Sedang menginstall Dependency"
    sudo apt install git nginx network-manager python3-pip python3-venv python3-websockets websocketd -y
    show_done "Selesai menginstall Dependecy"
}

configure_visudo() {
    show_progress "Sedang mengkonfigurasi visudo"

    # Buat file temporari untuk pengeditan
    sudo cp /etc/sudoers /tmp/sudoers.new
    sudo chmod 750 /tmp/sudoers.new

    # Tambahkan konfigurasi yang diperlukan
    echo "$ORIGINAL_USER ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /tmp/sudoers.new > /dev/null
    echo "www-data ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /tmp/sudoers.new > /dev/null

    # Validasi file sudoers
    sudo visudo -cf /tmp/sudoers.new
    if [ $? -eq 0 ]; then
        sudo cp /tmp/sudoers.new /etc/sudoers
        sudo chmod 440 /etc/sudoers
        show_done "Mengkonfigurasi visudo"
        return 0
    else
        echo "Error: File sudoers tidak valid!"
        sudo rm /tmp/sudoers.new
        return 1
    fi
}


# TANPA SUDO
clone_repo(){
    cd "$ORIGINAL_USER_HOME"
    git clone https://TOKEN@github.com/ChristoferRian/deauth-detector.git
}


# TANPA SUDO
setup_venv(){
    # cd "$ORIGINAL_USER_HOME/deauth-detector/be/" || { echo "Directory tidak ditemukan"; return 1; }
    python3 -m venv "$ORIGINAL_USER_HOME/deauth-detector/be/venv"
    source "$ORIGINAL_USER_HOME/deauth-detector/be/venv/bin/activate" || { echo "Gagal aktivasi venv"; return 1; }
    pip install -r "$ORIGINAL_USER_HOME/deauth-detector/be/requirements.txt"
}

# Konfigurasi Nginx (perlu sudo)
configure_nginx() {
    
    show_progress "move dan setting permission folder frontend"
    sudo mv "$ORIGINAL_USER_HOME/deauth-detector/fe2" /var/www/
    sudo chown -R www-data:www-data /var/www/fe2
    sudo chmod -R +777 /var/www/fe2
    
    # Buat file konfigurasi frontend
    show_progress "Membuat file konfigurasi frontend"
    
    
    cat > default << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    root /var/www/fe2;

    index index.html index.htm index.nginx-debian.html;
    # Remove hardcoded IP and use '_' to match any hostname
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
    sudo mv default /etc/nginx/sites-available/default    
    # Aktifkan konfigurasi Nginx
    show_progress "Mengaktifkan konfigurasi Nginx"
    sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
    
    # Periksa konfigurasi Nginx
    sudo nginx -t
    
    # Reload Nginx tanpa restart
    sudo systemctl reload nginx
    show_done "Mengaktifkan konfigurasi Nginx"
}


# SUDO
adding_cronjob(){
    
    if [ "$(id -u)" -ne 0 ]; then
        echo "Script ini harus dijalankan sebagai root atau dengan sudo"
        exit 1
    fi
    crontab -l > /tmp/current_crontab 2>/dev/null

# Memeriksa apakah cronjob sudah ada
    if grep -q "@reboot sleep 15 && bash $ORIGINAL_USER_HOME/deauth-detector/be/run_services.sh" /tmp/current_crontab; then
        echo "Cronjob sudah ada dalam crontab"
    else
    # Menambahkan cronjob baru
        echo "@reboot sleep 15 && bash $ORIGINAL_USER_HOME/deauth-detector/be/run_services.sh" >> /tmp/current_crontab
        crontab /tmp/current_crontab
        echo "Cronjob berhasil ditambahkan"
    fi

    # Membersihkan file temporary
    rm /tmp/current_crontab

    echo "Selesai!"
}


main(){
    # Ekspor variabel ke environment agar bisa diakses di semua proses
    export ORIGINAL_USER=$(logname || echo $SUDO_USER || echo $USER)
    export ORIGINAL_USER_HOME=$(eval echo ~$ORIGINAL_USER)
    
    # Simpan variabel-variabel ke file temporary
    echo "ORIGINAL_USER=$ORIGINAL_USER" > /tmp/deploy_vars
    echo "ORIGINAL_USER_HOME=$ORIGINAL_USER_HOME" >> /tmp/deploy_vars
    
    install_dependency
    configure_visudo

    # Gunakan source untuk membaca variabel dari file temporary
    sudo -u $ORIGINAL_USER bash -c "source /tmp/deploy_vars && cd $ORIGINAL_USER_HOME && export HOME=$ORIGINAL_USER_HOME && $(declare -f clone_repo show_progress show_done); clone_repo"
    sudo -u $ORIGINAL_USER bash -c "source /tmp/deploy_vars && cd $ORIGINAL_USER_HOME && export HOME=$ORIGINAL_USER_HOME && $(declare -f setup_venv show_progress show_done); setup_venv"

    configure_nginx
    adding_cronjob
    
    # Hapus file temporary
    rm -f /tmp/deploy_vars
    
    echo "=== PROSES OTOMASI SELESAI ==="
}

# Jalankan main jika script dijalankan langsung (bukan di-source)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi