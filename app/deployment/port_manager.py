import logging
import socket

logger = logging.getLogger(__name__)

class PortManager:
    """Intelligent port management for local and cloud deployments"""

    # Default port assignments (service name -> default port)
    PORT_ASSIGNMENTS = {
        'mcp_server': 8000,
        'swarm_coordinator': 8001,
        'agent_ui': 3000,
        'streamlit': 8501,
        'grafana': 3001,
        'prometheus': 9090,
        'redis': 6379,
        'websocket': 8080,
        'mcp_api': 8002,
        'ingress': 80,
        'analytics': 8081
    }

    def __init__(self):
        self.reserved_ports = set()
        self.dynamic_ports = {}

    def get_available_port(self, service: str, preferred: int | None = None) -> int:
        """Get available port with fallback strategy
        
        Prioritizes:
        1. Preferred port (if available)
        2. Default port (if available)
        3. Random available port
        """
        # First try preferred port
        if preferred and self.is_port_available(preferred):
            self.reserve_port(service, preferred)
            return preferred

        # Then try default assignment
        default = self.PORT_ASSIGNMENTS.get(service)
        if default and self.is_port_available(default):
            self.reserve_port(service, default)
            return default

        # Finally find any available port
        return self.find_random_available_port()

    def is_port_available(self, port: int) -> bool:
        """Check if port is available for binding"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except:
                return False

    def reserve_port(self, service: str, port: int):
        """Reserve a port for a specific service"""
        if port in self.reserved_ports:
            logger.warning(f"Port {port} already reserved")
            return

        self.reserved_ports.add(port)
        self.dynamic_ports[service] = port
        logger.info(f"✅ Port {port} reserved for {service}")

    def find_random_available_port(self, min_port: int = 3000, max_port: int = 65535) -> int:
        """Find a random available port within range"""
        for _ in range(5):  # Try up to 5 times
            port = random.randint(min_port, max_port)
            if self.is_port_available(port):
                self.reserve_port("dynamic", port)  # Use 'dynamic' to track in reserved_ports
                return port

        raise RuntimeError(f"Could not find an available port in range {min_port}-{max_port}")

    def get_service_port(self, service: str) -> int:
        """Get the port assigned to a specific service"""
        return self.dynamic_ports.get(service)

    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml with dynamic ports"""
        services = []
        for service, port in self.dynamic_ports.items():
            services.append(f"{service}: {port}")

        return f"""
version: '3'
services:
{chr(10).join(['  - ' + s for s in services])}
"""

# Example usage
if __name__ == "__main__":
    port_manager = PortManager()

    # Get ports for services
    mcp_port = port_manager.get_available_port('mcp_server')
    swarm_port = port_manager.get_available_port('swarm_coordinator')
    ui_port = port_manager.get_available_port('agent_ui')

    print(f"Assigned ports: MCP Server {mcp_port}, Swarm Coordinator {swarm_port}, UI {ui_port}")

    # Generate docker-compose
    print("\nGenerated docker-compose:\n")
    print(port_manager.generate_docker_compose())
