import unittest
import json
from app import app


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_get_rows_by_ids(self):
        response = self.app.get("/list/1,2,3")
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)

    def test_get_similar(self):
        response = self.app.get("/similar/1")
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)

    def test_post_ask(self):
        prompt_data = {"prompt": "How can I improve my programming skills?"}
        headers = {"Content-Type": "application/json"}
        response = self.app.post("/ask", data=json.dumps(prompt_data), headers=headers)
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

        # Check the response format based on the actual behavior
        self.assertIsInstance(data, list)
        self.assertTrue(len(data[0]) == 11, "The ask_id is not 11 characters long")
        # ... Other assertions as needed

    def test_post_ask_missing_prompt(self):
        prompt_data = {}
        headers = {"Content-Type": "application/json"}
        response = self.app.post("/ask", data=json.dumps(prompt_data), headers=headers)
        data = json.loads(response.data.decode())
        self.assertEqual(
            response.status_code, 400
        )  # Expect a 400 status code for missing prompt
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Prompt is required.")


if __name__ == "__main__":
    unittest.main()
