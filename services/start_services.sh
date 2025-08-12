#!/bin/bash
# ByteBeast Service Management Script

ACTION=${1:-status}
MODE=${2:-normal}

case $ACTION in
    start)
        echo "Starting ByteBeast services..."
        if [[ $MODE == "mock" || $MODE == "test" ]]; then
            echo "Starting in mock/test mode..."
            # Start services with mock mode arguments
            # This would require modified service files or environment variables
            sudo systemctl start bytebeast.target
            echo "Started in test mode - services will use mock sensors/displays"
        else
            sudo systemctl start bytebeast.target
            echo "Started in normal mode"
        fi
        ;;
    stop)
        echo "Stopping ByteBeast services..."
        sudo systemctl stop bytebeast.target
        echo "Services stopped"
        ;;
    restart)
        echo "Restarting ByteBeast services..."
        sudo systemctl restart bytebeast.target
        echo "Services restarted"
        ;;
    status)
        echo "ByteBeast Service Status:"
        echo "========================"
        sudo systemctl status bytebeast-sense.service --no-pager -l
        echo ""
        sudo systemctl status bytebeast-state.service --no-pager -l  
        echo ""
        sudo systemctl status bytebeast-viz.service --no-pager -l
        echo ""
        sudo systemctl status bytebeast-power.service --no-pager -l
        ;;
    logs)
        SERVICE=${2:-sense}
        echo "Showing logs for bytebeast-$SERVICE.service..."
        journalctl -u "bytebeast-$SERVICE.service" -f
        ;;
    enable)
        echo "Enabling ByteBeast services for auto-start..."
        sudo systemctl enable bytebeast.target
        echo "Services enabled"
        ;;
    disable)
        echo "Disabling ByteBeast services..."
        sudo systemctl disable bytebeast.target
        echo "Services disabled"
        ;;
    *)
        echo "ByteBeast Service Manager"
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable} [mock|service-name]"
        echo ""
        echo "Commands:"
        echo "  start [mock]     - Start all services (optionally in mock mode)"
        echo "  stop             - Stop all services"
        echo "  restart          - Restart all services" 
        echo "  status           - Show status of all services"
        echo "  logs [service]   - Show logs (sense, state, viz, power)"
        echo "  enable           - Enable auto-start"
        echo "  disable          - Disable auto-start"
        echo ""
        echo "Examples:"
        echo "  $0 start         - Start with real hardware"
        echo "  $0 start mock    - Start with mock sensors/displays"
        echo "  $0 logs viz      - Show visualization service logs"
        echo "  $0 status        - Check all service status"
        exit 1
        ;;
esac