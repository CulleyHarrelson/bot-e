var express = require('express');
var router = express.Router();
const axios = require('axios');

router.post('/', async function(req, res, next) {
  try {
    const { token, searchPhrase } = req.body;

    const recaptchaToken = req.body["token"];
    const secretKey = process.env.CAPTCHA_SECRET_KEY;

    // Verify the reCAPTCHA token with Google's reCAPTCHA API
    const response = await axios.post('https://www.google.com/recaptcha/api/siteverify', null, {
      params: {
        secret: secretKey,
        response: token,
      },
    });

    const { success, score } = response.data;

    // Check if the reCAPTCHA verification was successful and the score is acceptable
    if (success && score >= 0.5) {
      // Your reCAPTCHA validation is successful, and you can proceed with processing the searchPhrase
      res.json({ success: true });
    } else {
      // reCAPTCHA verification failed, possibly a bot
      res.json({ success: false });
    }
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ success: false });
  }
});

module.exports = router;
