import json
import pytest
from unittest.mock import patch, MagicMock

import flask_server


@pytest.fixture
def app():
    # Configure the Flask app for testing and return the app object
    app = flask_server.app
    app.config.update({
        "TESTING": True,
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_page(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_evaluate_mocked(client):
    # Prepare a fake response object with .text containing JSON
    fake_response = MagicMock()
    fake_response.text = json.dumps({"total_score": 10, "feedback": "Great job"})

    # Patch the generate_content method on the GenerativeModel class
    target = 'google.generativeai.GenerativeModel.generate_content'
    with patch(target, return_value=fake_response):
        resp = client.post('/evaluate', json={"pseudocode": "print('test')"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"total_score": 10, "feedback": "Great job"}


def test_empty_input_handling(client):
    # Send empty JSON or JSON without the 'pseudocode' key
    resp = client.post('/evaluate', json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data is not None and 'error' in data

 