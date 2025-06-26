import pytest
from flask import session
from app import app  # Import your Flask app from app.py


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.secret_key = 'test_secret'
    with app.test_client() as client:
        yield client


# --------- Test 1: Chatbot route - Force exception ----------
def test_chatbot_exception(client, monkeypatch):
    def bad_connection():
        raise Exception("DB failure")

    monkeypatch.setattr('app.get_db_connection', bad_connection)

    with client.session_transaction() as sess:
        sess['username'] = 'test_user'

    response = client.post('/chatbot', json={'message': 'last_order'})
    assert response.status_code == 200
    assert b"An error occurred" in response.data


# --------- Test 2: Add to cart - DB connection failure ----------
def test_add_to_cart_db_error(client, monkeypatch):
    monkeypatch.setattr('app.get_db_connection', lambda: None)

    with client.session_transaction() as sess:
        sess['username'] = 'test_user'
        sess['role'] = 'user'

    response = client.post('/add_to_cart', json={'id': 1, 'action': 'increase'})
    assert response.status_code == 500
    assert b"Database error" in response.data


# --------- Test 3: Add to cart - Unauthorized ----------
def test_add_to_cart_unauthorized(client):
    response = client.post('/add_to_cart', json={'id': 1, 'action': 'increase'})
    assert response.status_code == 401


# --------- Test 4: Checkout - No session user ----------
def test_checkout_not_logged_in(client):
    response = client.post('/checkout')
    assert response.status_code == 302  # Redirect to login


# --------- Test 5: Checkout - DB connection failure ----------
def test_checkout_db_error(client, monkeypatch):
    monkeypatch.setattr('app.get_db_connection', lambda: None)
    with client.session_transaction() as sess:
        sess['username'] = 'test_user'

    response = client.post('/checkout')
    assert response.status_code == 500
    assert b"Database error during checkout" in response.data


# --------- Test 6: Pull and Reload - Unauthorized Token ----------
def test_pull_and_reload_unauthorized(client):
    response = client.post('/pull_and_reload', headers={"X-Auth-Token": "wrong-token"})
    assert response.status_code == 401
    assert b"Unauthorized" in response.data


# --------- Test 7: Cart POST - Missing form data ----------
def test_cart_invalid_form_data(client):
    with client.session_transaction() as sess:
        sess['role'] = 'user'
        sess['username'] = 'test_user'

    response = client.post('/cart', data={})
    assert response.status_code == 302  # Redirect due to validation failure


# --------- Test 8: Chatbot - Message not understood ----------
def test_chatbot_default_response(client, monkeypatch):
    def dummy_connection():
        class DummyCursor:
            def execute(self, *args, **kwargs): pass
            def fetchone(self): return None
            def fetchall(self): return []

            def close(self): pass
        class DummyConnection:
            def cursor(self, dictionary=True): return DummyCursor()
            def close(self): pass
        return DummyConnection()

    monkeypatch.setattr('app.get_db_connection', dummy_connection)

    with client.session_transaction() as sess:
        sess['username'] = 'test_user'

    response = client.post('/chatbot', json={'message': 'random_message'})
    assert response.status_code == 200
    assert b"I'm sorry" in response.data


# --------- Test 9: Logout clears session ----------
def test_logout(client):
    with client.session_transaction() as sess:
        sess['username'] = 'test_user'
        sess['role'] = 'user'

    response = client.get('/logout')
    assert response.status_code == 302  # Redirect to login
