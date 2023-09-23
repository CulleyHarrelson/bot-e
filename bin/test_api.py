import json
import requests
import unittest


class APITestCase(unittest.TestCase):
    def setUp(self):
        # self.api_url = "http://snowball.bot-e.com"
        self.api_url = "http://localhost:6464"
        self.headers = {"Content-Type": "application/json"}

    def test_api_endpoint(self):
        prompt_data = {"question": "what is the meaning of human life?"}
        response = requests.post(
            f"{self.api_url}/ask", data=json.dumps(prompt_data), headers=self.headers
        )
        data = response.json()

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the response format based on the actual behavior
        # self.assertIsInstance(data, dict)
        self.assertTrue(
            len(data["question_id"]) == 11, "The question_id is not 11 characters long"
        )
        # ... Other assertions as needed


if __name__ == "__main__":
    unittest.main()
