import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    """Test that login page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'login' in response.data.lower()

def test_register_page(client):
    """Test that register page loads correctly"""
    response = client.get('/register')
    assert response.status_code == 200

def test_admin_login(client):
    """Test admin login functionality"""
    response = client.post('/', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200

@patch('app.get_db_connection')
def test_invalid_login_with_db_mock(mock_db, client):
    """Test invalid login attempt with mocked database"""
    # Mock database connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # No user found
    mock_connection.cursor.return_value = mock_cursor
    mock_db.return_value = mock_connection
    
    response = client.post('/', data={
        'username': 'invalid',
        'password': 'invalid'
    })
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

@patch('app.get_db_connection')
def test_database_connection_failure(mock_db, client):
    """Test behavior when database connection fails"""
    mock_db.return_value = None  # Simulate connection failure
    
    response = client.post('/', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert b'Database connection error' in response.data

def test_logout(client):
    """Test logout functionality"""
    # First login as admin (no DB required)
    client.post('/', data={
        'username': 'admin',
        'password': 'admin123'
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

def test_constants_defined():
    """Test that template constants are properly defined"""
    from app import LOGIN_TEMPLATE, REGISTER_TEMPLATE
    assert LOGIN_TEMPLATE == 'login.html'
    assert REGISTER_TEMPLATE == 'register.html'
