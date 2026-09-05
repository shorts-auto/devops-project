from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import os
import psycopg
from psycopg import sql
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ops Console</title>
    <style>
        :root { --ink: #17221b; --muted: #65736a; --paper: #f5f4ee; --panel: #fffef9; --line: #d9ded6; --green: #176b4b; --red: #b54738; }
        * { box-sizing: border-box; }
        body { margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.5 Georgia, serif; }
        header { padding: 42px max(24px, calc((100% - 1100px) / 2)); background: #193c2d; color: #f7f3e8; }
        header p { margin: 6px 0 0; color: #bfd2c5; }
        h1, h2 { margin: 0; font-weight: 500; letter-spacing: .01em; }
        main { max-width: 1100px; margin: 28px auto; padding: 0 24px 48px; }
        .layout { display: grid; grid-template-columns: minmax(280px, 350px) 1fr; gap: 24px; align-items: start; }
        .panel { padding: 24px; background: var(--panel); border: 1px solid var(--line); box-shadow: 5px 5px 0 #dce5d9; }
        label { display: block; margin: 18px 0 6px; color: var(--muted); font: 13px Arial, sans-serif; text-transform: uppercase; letter-spacing: .08em; }
        input, textarea, select, button { width: 100%; padding: 11px 12px; border: 1px solid #bdc8be; border-radius: 2px; background: #fff; color: var(--ink); font: inherit; }
        textarea { min-height: 110px; resize: vertical; }
        button { margin-top: 20px; border-color: var(--green); background: var(--green); color: white; cursor: pointer; font-family: Arial, sans-serif; font-weight: 700; }
        button:hover { background: #0f5238; }
        .toolbar { display: flex; gap: 10px; margin: 18px 0; }
        .toolbar select { max-width: 180px; }
        .incident { padding: 18px 0; border-bottom: 1px solid var(--line); }
        .incident:first-child { padding-top: 0; }
        .incident h3 { margin: 0 0 4px; font-size: 20px; font-weight: 500; }
        .incident p { margin: 5px 0 12px; color: var(--muted); }
        .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font: 12px Arial, sans-serif; }
        .badge { padding: 4px 8px; border-radius: 10px; background: #e6eee8; color: var(--green); text-transform: uppercase; }
        .badge.critical, .badge.high { background: #f9e3de; color: var(--red); }
        .status { margin-left: auto; width: auto; padding: 6px 8px; font-size: 12px; }
        .empty { color: var(--muted); text-align: center; padding: 36px 0; }
        .error { min-height: 24px; color: var(--red); font: 14px Arial, sans-serif; }
        @media (max-width: 760px) { .layout { grid-template-columns: 1fr; } main { margin-top: 18px; } }
    </style>
</head>
<body>
    <header><h1>Ops Console</h1><p>Track incidents from first signal to resolution.</p></header>
    <main>
        <div class="layout">
            <form class="panel" id="incident-form">
                <h2>Report an incident</h2>
                <label for="title">Title</label><input id="title" maxlength="200" required placeholder="API latency in production">
                <label for="severity">Severity</label>
                <select id="severity"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option><option value="critical">Critical</option></select>
                <label for="description">What is happening?</label><textarea id="description" placeholder="Add impact, symptoms, or useful links"></textarea>
                <div class="error" id="form-error"></div><button type="submit">Create incident</button>
            </form>
            <section class="panel">
                <h2>Incident queue</h2>
                <div class="toolbar"><select id="status-filter"><option value="">All statuses</option><option value="open">Open</option><option value="investigating">Investigating</option><option value="resolved">Resolved</option></select></div>
                <div id="incident-list"><p class="empty">Loading incidents...</p></div>
            </section>
        </div>
    </main>
    <script>
        const list = document.querySelector('#incident-list');
        const filter = document.querySelector('#status-filter');
        const formError = document.querySelector('#form-error');
        const incidentTitle = document.querySelector('#title');
        const incidentSeverity = document.querySelector('#severity');
        const incidentDescription = document.querySelector('#description');
        const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
        async function loadIncidents() {
            const query = filter.value ? `?status=${filter.value}` : '';
            const response = await fetch(`/api/incidents${query}`);
            const data = await response.json();
            if (!response.ok) { list.innerHTML = `<p class="empty">${escapeHtml(data.error)}</p>`; return; }
            list.innerHTML = data.incidents.length ? data.incidents.map(renderIncident).join('') : '<p class="empty">No incidents yet.</p>';
        }
        function renderIncident(item) {
            return `<article class="incident"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description || 'No description provided.')}</p><div class="meta"><span class="badge ${item.severity}">${item.severity}</span><span>${new Date(item.created_at).toLocaleString()}</span><select class="status" data-id="${item.id}"><option ${item.status === 'open' ? 'selected' : ''}>open</option><option ${item.status === 'investigating' ? 'selected' : ''}>investigating</option><option ${item.status === 'resolved' ? 'selected' : ''}>resolved</option></select></div></article>`;
        }
        document.querySelector('#incident-form').addEventListener('submit', async event => {
            event.preventDefault(); formError.textContent = '';
            const response = await fetch('/api/incidents', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({title: incidentTitle.value, severity: incidentSeverity.value, description: incidentDescription.value}) });
            if (!response.ok) { formError.textContent = (await response.json()).error; return; }
            event.target.reset(); await loadIncidents();
        });
        filter.addEventListener('change', loadIncidents);
        list.addEventListener('change', async event => {
            if (!event.target.matches('.status')) return;
            await fetch(`/api/incidents/${event.target.dataset.id}`, { method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({status: event.target.value}) });
            await loadIncidents();
        });
        loadIncidents().catch(() => { list.innerHTML = '<p class="empty">The database is unavailable.</p>'; });
    </script>
</body>
</html>
"""

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
@app.route('/dashboard')
def dashboard():
    """Render the operations console."""
    return render_template_string(DASHBOARD_TEMPLATE)


def ensure_incidents_table(conn):
    """Create the incident table when the application is first used."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            severity VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()


def incident_to_dict(row):
    """Convert a database row into the public API shape."""
    return {
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'severity': row[3],
        'status': row[4],
        'created_at': row[5].isoformat() if row[5] else None,
        'updated_at': row[6].isoformat() if row[6] else None,
    }


@app.route('/api/incidents', methods=['GET', 'POST'])
def incidents():
    """List incidents or create a new incident."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503

    try:
        ensure_incidents_table(conn)
        cursor = conn.cursor()
        if request.method == 'GET':
            status = request.args.get('status')
            if status and status not in {'open', 'investigating', 'resolved'}:
                return jsonify({'error': 'Invalid status filter'}), 400
            query = (
                "SELECT id, title, description, severity, status, created_at, updated_at "
                "FROM incidents"
            )
            params = ()
            if status:
                query += " WHERE status = %s"
                params = (status,)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            return jsonify({'incidents': [incident_to_dict(row) for row in cursor.fetchall()]}), 200

        payload = request.get_json(silent=True) or {}
        title = str(payload.get('title', '')).strip()
        description = str(payload.get('description', '')).strip()
        severity = payload.get('severity', 'medium')
        if not title or len(title) > 200:
            return jsonify({'error': 'Title is required and must be 200 characters or fewer'}), 400
        if severity not in {'low', 'medium', 'high', 'critical'}:
            return jsonify({'error': 'Invalid severity'}), 400
        cursor.execute(
            "INSERT INTO incidents (title, description, severity) VALUES (%s, %s, %s) "
            "RETURNING id, title, description, severity, status, created_at, updated_at",
            (title, description, severity)
        )
        incident = incident_to_dict(cursor.fetchone())
        conn.commit()
        return jsonify(incident), 201
    except Exception as error:
        conn.rollback()
        logger.error(f"Incident operation error: {str(error)}")
        return jsonify({'error': 'Unable to process incident'}), 500
    finally:
        conn.close()


@app.route('/api/incidents/<int:incident_id>', methods=['PATCH', 'DELETE'])
def incident_detail(incident_id):
    """Update or remove an incident."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 503
    try:
        ensure_incidents_table(conn)
        cursor = conn.cursor()
        if request.method == 'DELETE':
            cursor.execute("DELETE FROM incidents WHERE id = %s", (incident_id,))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Incident not found'}), 404
            conn.commit()
            return '', 204

        payload = request.get_json(silent=True) or {}
        status = payload.get('status')
        if status not in {'open', 'investigating', 'resolved'}:
            return jsonify({'error': 'Invalid status'}), 400
        cursor.execute(
            "UPDATE incidents SET status = %s, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = %s RETURNING id, title, description, severity, status, created_at, updated_at",
            (status, incident_id)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Incident not found'}), 404
        conn.commit()
        return jsonify(incident_to_dict(row)), 200
    except Exception as error:
        conn.rollback()
        logger.error(f"Incident update error: {str(error)}")
        return jsonify({'error': 'Unable to update incident'}), 500
    finally:
        conn.close()

@app.route('/health/live')
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

@app.route('/api/init-db', methods=['GET', 'POST'])
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
