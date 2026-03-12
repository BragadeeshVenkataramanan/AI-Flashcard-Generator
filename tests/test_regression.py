import json
from app import app 

def test_pdf_generation_regression():
    client = app.test_client()
    data = {
        "title": "Regression Test",
        "cards": [{"question": "Q1", "answer": "A1"}]
    }
    response = client.post("/export/pdf", json=data)
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert len(response.data) > 0  # Ensure actual content is present
