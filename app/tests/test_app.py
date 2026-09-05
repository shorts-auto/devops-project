import pytest
from app import app, get_db_connection
import os
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test main health endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['service'] == 'myapp'
    
    def test_readiness_endpoint_no_db(self, client):
        """Test readiness endpoint when database is unavailable"""
        with patch('app.get_db_connection', return_value=None):
            response = client.get('/health/ready')
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'not ready'
    
    def test_readiness_endpoint_with_db(self, client):
        """Test readiness endpoint when database is available"""
        mock_conn = MagicMock()
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.get('/health/ready')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ready'

class TestStatusEndpoint:
    """Test status endpoint"""
    
    def test_status_endpoint_success(self, client):
        """Test status endpoint when database is connected"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('PostgreSQL 15.0',)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.get('/api/status')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'running'
            assert data['database'] == 'connected'
    
    def test_status_endpoint_no_db(self, client):
        """Test status endpoint when database is disconnected"""
        with patch('app.get_db_connection', return_value=None):
            response = client.get('/api/status')
            assert response.status_code == 503
            data = response.get_json()
            assert data['database'] == 'disconnected'


class TestIncidentWorkflow:
    """Test the incident tracking workflow."""

    def test_dashboard_is_available(self, client):
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Ops Console' in response.data
        assert b'Report an incident' in response.data

    def test_create_incident_requires_title(self, client):
        mock_conn = MagicMock()
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.post('/api/incidents', json={'severity': 'high'})
            assert response.status_code == 400
            assert 'Title is required' in response.get_json()['error']

    def test_create_incident_success(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1, 'API latency', 'Requests are slow', 'high', 'open',
            None, None
        )
        mock_conn.cursor.return_value = mock_cursor
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.post('/api/incidents', json={
                'title': 'API latency',
                'description': 'Requests are slow',
                'severity': 'high'
            })
            assert response.status_code == 201
            assert response.get_json()['status'] == 'open'
            mock_conn.commit.assert_called()

class TestInitDB:
    """Test database initialization endpoint"""
    
    def test_init_db_success(self, client):
        """Test successful database initialization"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.post('/api/init-db')
            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data
    
    def test_init_db_no_connection(self, client):
        """Test database initialization when connection fails"""
        with patch('app.get_db_connection', return_value=None):
            response = client.post('/api/init-db')
            assert response.status_code == 500

class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('public', 'users')]
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.get_db_connection', return_value=mock_conn):
            response = client.get('/metrics')
            assert response.status_code == 200
            assert 'application_info' in response.data.decode()

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
