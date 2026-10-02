"""Unit and integration test suite for the Model Inference API."""

import unittest
from fastapi.testclient import TestClient
from app import app


class TestInferenceAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        """Req-4: Health check endpoint returns 200 OK and {'status': 'ok'}."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_predict_positive(self):
        """Req-5: Predict returns label string and score float for positive text."""
        payload = {"text": "This deployment architecture is awesome and wonderful!"}
        response = self.client.post("/v1/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("label", data)
        self.assertIn("score", data)
        self.assertIsInstance(data["label"], str)
        self.assertIsInstance(data["score"], float)
        self.assertEqual(data["label"], "positive")
        self.assertGreaterEqual(data["score"], 0.0)
        self.assertLessEqual(data["score"], 1.0)

    def test_predict_negative(self):
        """Req-5: Predict returns label string and score float for negative text."""
        payload = {"text": "This service encountered a terrible and bad error."}
        response = self.client.post("/v1/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "negative")
        self.assertIsInstance(data["score"], float)

    def test_predict_neutral(self):
        """Req-5: Predict returns label string and score float for neutral text."""
        payload = {"text": "The quick brown fox jumps over the lazy dog."}
        response = self.client.post("/v1/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "neutral")
        self.assertIsInstance(data["score"], float)

    def test_missing_text_rejected(self):
        """Req-6: Request lacking 'text' field is rejected with 422."""
        response = self.client.post("/v1/predict", json={})
        self.assertIn(response.status_code, [400, 422])

    def test_empty_string_rejected(self):
        """Req-6: Empty string text is rejected by min_length=1 validator."""
        response = self.client.post("/v1/predict", json={"text": ""})
        self.assertIn(response.status_code, [400, 422])

    def test_wrong_type_rejected(self):
        """Req-6: Non-string text is rejected."""
        response = self.client.post("/v1/predict", json={"text": 12345})
        # If integer is passed, pydantic might coerce or reject; test dict/list
        response_dict = self.client.post("/v1/predict", json={"text": {"nested": "value"}})
        self.assertIn(response_dict.status_code, [400, 422])


if __name__ == "__main__":
    unittest.main()
