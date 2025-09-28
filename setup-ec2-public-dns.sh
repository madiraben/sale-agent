#!/bin/bash
# Complete EC2 Setup Script with Public DNS and SSL
# Run this on your EC2 instance

set -e

echo "🚀 Setting up Messenger Chatbot on EC2 with Public DNS..."

# Get public DNS
PUBLIC_DNS=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
echo "📍 Your EC2 Public DNS: $PUBLIC_DNS"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "🔧 Installing dependencies..."
sudo apt install python3 python3-pip curl nginx openssl git -y

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "⚡ Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Setup project directory
echo "📁 Setting up project..."
cd ~/sale-agent || { echo "❌ Please upload your project to ~/sale-agent first"; exit 1; }

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
uv sync

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔐 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your Facebook credentials"
    echo "Current .env file:"
    cat .env
    read -p "Press enter to continue..."
fi

# Create SSL certificates
echo "🔒 Creating SSL certificates..."
sudo mkdir -p /etc/ssl/private

# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt \
  -subj "/C=US/ST=AWS/L=EC2/O=MessengerBot/CN=$PUBLIC_DNS"

echo "✅ SSL certificate created"

# Create nginx configuration
echo "🌐 Configuring nginx..."
sudo tee /etc/nginx/sites-available/messenger-webhook > /dev/null <<EOF
server {
    listen 80;
    server_name $PUBLIC_DNS;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name $PUBLIC_DNS;

    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/messenger-webhook /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx

# Create systemd service
echo "🔄 Creating systemd service..."
sudo tee /etc/systemd/system/messenger-bot.service > /dev/null <<EOF
[Unit]
Description=Messenger Chatbot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$HOME/sale-agent
Environment=PATH=$HOME/.local/bin:/usr/bin:/bin
ExecStart=$HOME/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start services
echo "▶️  Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable messenger-bot
sudo systemctl start messenger-bot

# Wait a moment for services to start
sleep 3

# Test the setup
echo "🧪 Testing the setup..."
echo "Testing HTTP (should redirect to HTTPS):"
curl -I "http://$PUBLIC_DNS/" || echo "HTTP test completed"

echo ""
echo "Testing HTTPS webhook:"
WEBHOOK_RESPONSE=$(curl -sk "https://$PUBLIC_DNS/webhook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=123")
echo "Response: $WEBHOOK_RESPONSE"

# Show service status
echo ""
echo "📊 Service status:"
sudo systemctl status messenger-bot --no-pager --lines=5

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌍 Your webhook URLs:"
echo "   HTTP:  http://$PUBLIC_DNS/webhook"
echo "   HTTPS: https://$PUBLIC_DNS/webhook"
echo ""
echo "🔗 Facebook Webhook URL: https://$PUBLIC_DNS/webhook"
echo "🔑 Verify Token: 123"
echo ""
echo "⚠️  Note: This uses a self-signed SSL certificate."
echo "   Facebook should accept it, but browsers will show a warning."
echo ""
echo "📝 Useful commands:"
echo "   Check logs: sudo journalctl -u messenger-bot -f"
echo "   Restart bot: sudo systemctl restart messenger-bot"
echo "   Restart nginx: sudo systemctl restart nginx"
echo "   Test webhook: curl -k 'https://$PUBLIC_DNS/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=123'"
echo ""
echo "🎉 Ready for Facebook Messenger integration!"