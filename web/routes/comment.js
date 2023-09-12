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
      console.log("got an error")
    }
    else {
      try {

          const recaptchaToken = req.body["recaptcha_token"];
          const secretKey = process.env.CAPTCHA_SECRET_KEY;

          const verificationURL = `https://www.google.com/recaptcha/api/siteverify?secret=${secretKey}&response=${recaptchaToken}`;
          const verificationResponse = await axios.post(verificationURL);

          if (verificationResponse.data.success) {
            if (verificationResponse.data.score > 0.5) {
              const apiResponse = await axios.post('http://127.0.0.1:6464/add_comment', { question_id: req.body.question_id,  session_id: req.body.session_id, comment: req.body.comment });
              if (apiResponse.data[0] > 0) {
                return res.json({ success: true });
              } else {
                return res.json({ success: false, error: 'Comment addition failed.' });
              }

            } else {
              return res.json({ success: false, error: 'CAPTCHA verification failed because of score.' });
            }
          } else {
              return res.json({ success: false, error: 'CAPTCHA verification failed.' });
          }

      } catch (err) {
        res.render('comment', { title: 'bot-e', errors: [{msg: 'There was an error sending the comment to the API.'}] });
      }
    }
});

module.exports = router;
