import unittest
import json
from api import app


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_get_rows_by_ids(self):
        response = self.app.get("/list/1,2,3")
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)

    def test_post_question(self):
        prompt_data = {"question": "what is the meaning of human life?"}
        headers = {"Content-Type": "application/json"}
        response = self.app.post("/ask", data=json.dumps(prompt_data), headers=headers)
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

        # Check the response format based on the actual behavior
        self.assertIsInstance(data, dict)
        self.assertTrue(
            len(data["question_id"]) == 11, "The question_id is not 11 characters long"
        )
        # ... Other assertions as needed

    def test_post_question_missing_prompt(self):
        prompt_data = {}
        headers = {"Content-Type": "application/json"}
        response = self.app.post("/ask", data=json.dumps(prompt_data), headers=headers)
        data = json.loads(response.data.decode())
        self.assertEqual(
            response.status_code, 400
        )  # Expect a 400 status code for missing prompt
        self.assertIn("error", data)
        self.assertEqual(data["error"], "question is required.")


if __name__ == "__main__":
    unittest.main()
