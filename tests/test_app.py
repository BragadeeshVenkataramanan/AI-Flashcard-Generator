import unittest
from unittest.mock import patch
from app import app

class FlashcardAppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_index_route_get(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Flashcards", response.data)

    @patch("app.generate_with_gemini")
    def test_generate_flashcards_gemini(self, mock_generate):
        mock_generate.return_value = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]

        response = self.client.post("/", data={
            "topic": "Python",
            "provider": "gemini",
            "count": "2"
        })
        self.assertEqual(response.status_code, 200)
        mock_generate.assert_called_once_with("Python", 2, "standard")
        self.assertIn(b"Q1", response.data)

    # ------ Test PDF Export ------
    def test_export_pdf(self):
        data = {
            "title": "Test PDF",
            "cards": [{"question": "Test Q", "answer": "Test A"}]
        }
        response = self.client.post("/export/pdf", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")

    def test_export_csv(self):
        data = {
            "cards": [{"question": "Test Q", "answer": "Test A"}]
        }
        response = self.client.post("/export/csv", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"Test Q", response.data)

if __name__ == "__main__":
    unittest.main()
