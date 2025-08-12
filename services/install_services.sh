#!/bin/bash
# ByteBeast Service Installation Script

set -e

echo "Installing ByteBeast systemd services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please run this script as a regular user, not as root"
   exit 1
fi

# Service directory
SERVICE_DIR="/home/jerry/dev/bytebeast/services/systemd"
SYSTEMD_DIR="/etc/systemd/system"

echo "Copying service files..."
sudo cp "$SERVICE_DIR"/*.service "$SYSTEMD_DIR/"
sudo cp "$SERVICE_DIR"/*.target "$SYSTEMD_DIR/"

echo "Setting permissions..."
sudo chmod 644 "$SYSTEMD_DIR"/bytebeast-*.service
sudo chmod 644 "$SYSTEMD_DIR"/bytebeast.target

echo "Making service scripts executable..."
chmod +x "/home/jerry/dev/bytebeast/services"/*.py

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling ByteBeast services..."
sudo systemctl enable bytebeast-sense.service
sudo systemctl enable bytebeast-state.service  
sudo systemctl enable bytebeast-viz.service
sudo systemctl enable bytebeast-power.service
sudo systemctl enable bytebeast.target

echo ""
echo "ByteBeast services installed successfully!"
echo ""
echo "To start all services:"
echo "  sudo systemctl start bytebeast.target"
echo ""
echo "To check service status:"
echo "  sudo systemctl status bytebeast-*"
echo ""
echo "To view logs:"
echo "  journalctl -u bytebeast-sense.service -f"
echo "  journalctl -u bytebeast-state.service -f"
echo "  journalctl -u bytebeast-viz.service -f"
echo "  journalctl -u bytebeast-power.service -f"
echo ""
echo "To start in test mode (without hardware):"
echo "  sudo systemctl start bytebeast-sense@mock.service"
echo "  (Edit service files to add @mock instance if needed)"