#!/bin/bash

# Exit on error
set -e

echo "=== Ngrok Setup for Raspberry Pi ==="

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list && sudo apt update && sudo apt install ngrok
else
    echo "Ngrok is already installed."
fi

# Ask for Authtoken if not already configured
echo ""
echo "Please enter your Ngrok Authtoken from https://dashboard.ngrok.com/get-started/your-authtoken"
read -p "Authtoken: " NGKO_AUTH_TOKEN

if [ -z "$NGKO_AUTH_TOKEN" ]; then
    echo "Authtoken cannot be empty."
    exit 1
fi

ngrok config add-authtoken $NGKO_AUTH_TOKEN

# Configure static domain
STATIC_DOMAIN="ridgy-collin-gardenless.ngrok-free.dev"
APP_PORT=5000

echo ""
echo "Configuring Ngrok for domain: $STATIC_DOMAIN"

# Create/Update config file
# Default config location for ngrok service is usually in /etc/ngrok.yml or defined in service file
# We will use the default user config first to test, then setup service.

# Create a config file for the service
sudo tee /etc/ngrok.yml > /dev/null <<EOF
version: "2"
authtoken: $NGKO_AUTH_TOKEN
tunnels:
  backend:
    proto: http
    addr: $APP_PORT
    domain: $STATIC_DOMAIN
EOF

echo "Configuration saved to /etc/ngrok.yml"

# Install as system service
echo ""
echo "Installing Ngrok as a system service..."
sudo ngrok service install --config /etc/ngrok.yml

echo "Starting Ngrok service..."
sudo ngrok service start
sudo ngrok service status

echo ""
echo "=== Setup Complete ==="
echo "Your backend should now be accessible at: https://$STATIC_DOMAIN"
echo "API Health Check: https://$STATIC_DOMAIN/api/health"
