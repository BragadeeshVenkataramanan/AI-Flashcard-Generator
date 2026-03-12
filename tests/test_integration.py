# tests/test_integration.py
import json
from app import app

def test_generate_then_export_csv():
    client = app.test_client()

    # Step 1: Generate flashcards
    response = client.post("/", data={
        "topic": "Python",
        "provider": "ollama",
        "count": "3"
    })
    assert response.status_code == 200
    assert b"Python" in response.data  # Flashcards visible in output

    # Step 2: Export to CSV
    cards = [
        {"question": "What is Python?", "answer": "A programming language."},
        {"question": "Creator?", "answer": "Guido van Rossum"},
    ]
    export_response = client.post(
        "/export/csv",
        data=json.dumps({"cards": cards}),
        content_type="application/json"
    )
    assert export_response.status_code == 200
    assert export_response.mimetype == "text/csv"
    assert b"What is Python?" in export_response.data
