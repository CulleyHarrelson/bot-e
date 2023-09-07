var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');
var axios = require('axios');  // <-- Require axios


/* POST home page. */
router.post('/', 
  [
    check('question_id', 'question_id is required').trim().isLength({ min: 1 }).escape(),
    check('session_id', 'session_id is required').trim().isLength({ min: 1 }).escape(),
    check('direction', 'direction is required').trim().isLength({ min: 1 }).escape(),
    check('recaptcha_token', 'recaptcha_token is required').trim().isLength({ min: 1 }).escape()

  ],
  async (req, res) => {  // <-- Make the callback async
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // There are errors. Render the form again with sanitized values and error messages.
      res.json({ success: false });
    }
    else {
      try {
        // Extract the reCAPTCHA token from the request
        const recaptchaToken = req.body["recaptcha_token"];
        const question_id = req.body["question_id"];
        const session_id = req.sessionID
        const direction = req.body["direction"];
        const secretKey = process.env.CAPTCHA_SECRET_KEY;

        // Send the token to Google's reCAPTCHA API for verification
        const verificationURL = `https://www.google.com/recaptcha/api/siteverify?secret=${secretKey}&response=${recaptchaToken}`;
        const verificationResponse = await axios.post(verificationURL);

        // Check if the verification was successful
        if (verificationResponse.data.success) {
          if (verificationResponse.data.score > 0.5) {
            post_data = { question_id: question_id, session_id: session_id, direction: direction };
            const apiResponse = await axios.post('http://127.0.0.1:6464/next_question', post_data);
            res.json({ success: true, question_id: apiResponse.data['question_id'] });
          } else {
            res.json({ success: false });
          }
        } else {
            // Handle the failed CAPTCHA verification
            res.json({ success: false });
        }

      } catch (err) {
        // Handle error (e.g., API server might be down or there was a network error)
        res.json({ success: false });
      }
    }
});

module.exports = router;
