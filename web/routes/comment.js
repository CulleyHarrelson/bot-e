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
          const apiServer = req.app.locals.apiServer;

          const verificationURL = `https://www.google.com/recaptcha/api/siteverify?secret=${secretKey}&response=${recaptchaToken}`;
          const verificationResponse = await axios.post(verificationURL);

          if (verificationResponse.data.success) {
            if (verificationResponse.data.score > 0.5) {
              const apiResponse = await axios.post(`${apiServer}/add_comment`, { question_id: req.body.question_id,  session_id: req.body.session_id, comment: req.body.comment });
              //console.log("after api call");
              if (apiResponse.request.res.statusCode == 200) {
                return_value = { success: true };
                return res.json(return_value);
              } else {
                return res.json({ success: false, error: 'Comment addition failed.' });
              }

            } else {
              //console.log('CAPTCHA verification failed because of score.');
              return res.json({ success: false, error: 'CAPTCHA verification failed because of score.' });
            }
          } else {
              //console.log(verificationResponse.data);
              return res.json({ success: false, error: 'CAPTCHA verification failed.' });
          }

      } catch (err) {
        res.render('comment', { title: 'bot-e', errors: [{msg: 'There was an error sending the comment to the API.'}] });
      }
    }
});

module.exports = router;
