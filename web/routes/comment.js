var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');
var axios = require('axios');  // <-- Require axios

// TODO - disable search engine access

router.post('/', 
  [
    check('comment', 'comment is required').trim().isLength({ min: 1 }).escape(),
    // these are hidden fields, not sure what would happen if they were missing
    check('question_id', 'question_id is required').trim().isLength({ min: 1 }).escape(),
    check('session_id', 'session_id is required').trim().isLength({ min: 1 }).escape()
  ],
  async (req, res) => {  
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      res.render('comment', { title: 'bot-e question comment', errors: errors.array() });
    }
    else {
      try {

          const recaptchaToken = req.body["g-recaptcha-response"];
          const secretKey = process.env.CAPTCHA_SECRET_KEY;

          // Send the token to Google's reCAPTCHA API for verification
          const verificationURL = `https://www.google.com/recaptcha/api/siteverify?secret=${secretKey}&response=${recaptchaToken}`;
          const verificationResponse = await axios.post(verificationURL);

          // Check if the verification was successful
          if (verificationResponse.data.success) {
            if (verificationResponse.data.score > 0.5) {
              const apiResponse = await axios.post('http://127.0.0.1:6464/new_comment', { question_id: req.body.question,  session_id: req.body.session_id, comment: req.body.comment });
              res.redirect("/question/" + req.body.question);
            } else {
              res.render('comment', { title: 'bot-e', errors: ["CAPTCHA verification failed."] });
            }
          } else {
              // Handle the failed CAPTCHA verification
              res.render('comment', { title: 'bot-e', errors: ["CAPTCHA verification failed."] });
          }

      } catch (err) {
        // Handle error (e.g., API server might be down or there was a network error)
        res.render('comment', { title: 'bot-e', errors: [{msg: 'There was an error sending the comment to the API.'}] });
      }
    }
});

module.exports = router;
