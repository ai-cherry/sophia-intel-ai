"""
SOPHIA Intel MCP Server - Production Flask Application
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
import sys

# Add shared modules to path
sys.path.append('/app/shared')

# Import shared secret manager
from secret_manager import SecretManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Enable CORS for all origins (required for frontend-backend interaction)
    CORS(app, origins="*")
    
    # Get service name from environment or directory
    service_name = os.getenv('MCP_SERVICE_NAME', 'unknown')
    
    # Initialize secret manager
    secret_manager = SecretManager(service_name)
    
    # Store secret manager in app config for access in routes
    app.config['SECRET_MANAGER'] = secret_manager
    app.config['SERVICE_NAME'] = service_name
    
    # Validate secrets on startup
    validation = secret_manager.validate_service_secrets()
    if not validation['valid']:
        logger.warning(f"Service {service_name} missing required secrets: {validation['missing_secrets']}")
    
    # Register blueprints based on service
    try:
        if service_name == 'telemetry':
            from routes.telemetry import telemetry_bp
            app.register_blueprint(telemetry_bp, url_prefix='/api/v1')
        elif service_name == 'embedding':
            from routes.embedding import embedding_bp
            app.register_blueprint(embedding_bp, url_prefix='/api/v1')
        elif service_name == 'research':
            from routes.research import research_bp
            app.register_blueprint(research_bp, url_prefix='/api/v1')
        elif service_name == 'notion-sync':
            from routes.notion import notion_bp
            app.register_blueprint(notion_bp, url_prefix='/api/v1')
        else:
            logger.warning(f"Unknown service name: {service_name}")
    except ImportError as e:
        logger.error(f"Failed to import routes for {service_name}: {e}")
    
    # Global health endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """Global health check"""
        return jsonify({
            "service": f"{service_name}-mcp",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "secrets_valid": validation['valid']
        })
    
    # Global secret status endpoint
    @app.route('/secrets/status', methods=['GET'])
    def secret_status():
        """Get secret configuration status"""
        return jsonify(secret_manager.get_secret_status())
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    logger.info(f"Flask app created for service: {service_name}")
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
