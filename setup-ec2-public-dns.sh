#!/bin/bash
# Complete EC2 Setup Script with Public DNS and SSL
# Run this on your EC2 instance

set -e

echo "🚀 Setting up Messenger Chatbot on EC2 with Public DNS..."

# Option 1: Use your custom domain (RECOMMENDED)
# Uncomment and set your domain name:
PUBLIC_DNS="social-sale-agent-webhook.click"

# Option 2: Auto-detect (fallback to IP if no DNS)
if [ -z "$PUBLIC_DNS" ]; then
    PUBLIC_DNS=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
    if [ -z "$PUBLIC_DNS" ]; then
        PUBLIC_DNS=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
        if [ -z "$PUBLIC_DNS" ]; then
            # Fallback to your known public IP
            PUBLIC_DNS="18.141.189.40"
            echo "📍 No public DNS/IP from metadata, using hardcoded IP: $PUBLIC_DNS"
        else
            echo "📍 No public DNS found, using Public IP: $PUBLIC_DNS"
        fi
    else
        echo "📍 Your EC2 Public DNS: $PUBLIC_DNS"
    fi
fi

# Debug: Show what we got
echo "🔍 Debug - PUBLIC_DNS value: '$PUBLIC_DNS'"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "🔧 Installing dependencies..."
sudo apt install python3 python3-pip curl nginx openssl git snapd -y

# Install certbot for Let's Encrypt SSL
echo "🔐 Installing Certbot for SSL certificates..."
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

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

# Check if domain is using an IP (no Let's Encrypt) or real domain (use Let's Encrypt)
if [[ $PUBLIC_DNS =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "🔓 Using self-signed certificate for IP address"
    # Generate self-signed certificate for IP
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/ssl/private/nginx-selfsigned.key \
      -out /etc/ssl/certs/nginx-selfsigned.crt \
      -subj "/C=US/ST=AWS/L=EC2/O=MessengerBot/CN=$PUBLIC_DNS"
    SSL_CERT="/etc/ssl/certs/nginx-selfsigned.crt"
    SSL_KEY="/etc/ssl/private/nginx-selfsigned.key"
else
    echo "🔒 Using Let's Encrypt certificate for domain: $PUBLIC_DNS"
    # Wait for DNS to propagate
    echo "⏳ Waiting 30 seconds for DNS to propagate..."
    sleep 30
    
    # Test DNS resolution
    echo "🧪 Testing DNS resolution..."
    nslookup $PUBLIC_DNS || echo "⚠️ DNS might not be fully propagated yet"
    
    # Get Let's Encrypt certificate
    sudo certbot certonly --nginx --non-interactive --agree-tos --email admin@$PUBLIC_DNS -d $PUBLIC_DNS || {
        echo "⚠️ Let's Encrypt failed, falling back to self-signed certificate"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
          -keyout /etc/ssl/private/nginx-selfsigned.key \
          -out /etc/ssl/certs/nginx-selfsigned.crt \
          -subj "/C=US/ST=AWS/L=EC2/O=MessengerBot/CN=$PUBLIC_DNS"
        SSL_CERT="/etc/ssl/certs/nginx-selfsigned.crt"
        SSL_KEY="/etc/ssl/private/nginx-selfsigned.key"
    }
    
    # Set certificate paths for Let's Encrypt
    if [ -f "/etc/letsencrypt/live/$PUBLIC_DNS/fullchain.pem" ]; then
        SSL_CERT="/etc/letsencrypt/live/$PUBLIC_DNS/fullchain.pem"
        SSL_KEY="/etc/letsencrypt/live/$PUBLIC_DNS/privkey.pem"
        echo "✅ Let's Encrypt certificate obtained successfully"
    fi
fi

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

    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    
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