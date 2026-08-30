from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import os
import psycopg
from psycopg import sql
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'dbname': os.environ.get('DB_NAME', 'appdb'),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': os.environ.get('DB_PORT', 5432)
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

@app.route('/')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'myapp'
    }), 200

@app.route('/health/ready')
def readiness():
    """Readiness probe - checks database connectivity"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ready'}), 200
    return jsonify({'status': 'not ready'}), 503

@app.route('/api/status')
def api_status():
    """Get detailed application status"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return jsonify({
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'db_version': db_version
            }), 200
        else:
            return jsonify({
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'disconnected',
                'error': 'Cannot connect to database'
            }), 503
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/init-db')
def init_db():
    """Initialize database with sample tables"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Create sample table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Database initialized successfully")
        return jsonify({'message': 'Database initialized'}), 200
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT schemaname, tablename FROM pg_tables 
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """)
            tables = cursor.fetchall()
            cursor.close()
            conn.close()
            
            metrics_output = f"""# HELP application_info Application information
# TYPE application_info gauge
application_info{{service="myapp",version="1.0.0"}} 1

# HELP database_tables_count Number of tables in database
# TYPE database_tables_count gauge
database_tables_count {len(tables)}
"""
            return metrics_output, 200, {'Content-Type': 'text/plain'}
        else:
            return "database_connectivity 0\n", 503
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        return f"# Error: {str(e)}\n", 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting application")
    app.run(host='0.0.0.0', port=8000, debug=False)
