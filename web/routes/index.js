var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');
var axios = require('axios');  // <-- Require axios

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Bot-E', description: 'Bot-E: advice column 2.0.  What\'s going on?', canonical: 'https://bot-e/' });
});

router.post('/', 
  [
    check('question', 'question is required').trim().isLength({ min: 1 }).escape()
  ],
  async (req, res) => {  
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // There are errors. Render the form again with sanitized values and error messages.
      res.render('index', { title: 'Bot-E', errors: errors.array() });
    }
    else {
      //console.log("step 3")
      try {

          const apiServer = req.app.locals.apiServer;

          // Extract the reCAPTCHA token from the request
          const recaptchaToken = req.body["g-recaptcha-response"];
          const secretKey = process.env.CAPTCHA_SECRET_KEY;

          // Send the token to Google's reCAPTCHA API for verification
          const verificationURL = `https://www.google.com/recaptcha/api/siteverify?secret=${secretKey}&response=${recaptchaToken}`;
          const verificationResponse = await axios.post(verificationURL);
          //console.log(verificationResponse)

          // Check if the verification was successful
          if (verificationResponse.data.success) {
            if (verificationResponse.data.score > 0.5) {
              //console.log("step 6")
              //console.log("reCAPTCHA Score:", verificationResponse.data.score);
              try {
                const apiResponse = await axios.post(`${apiServer}/ask`, { question: req.body.question });
                res.redirect("/question/" + apiResponse.data['question_id']);
              } catch (err) {
                res.render('index', { title: 'Bot-E', errors: [err] });
              }
            } else {
              res.render('index', { title: 'Bot-E', errors: ["CAPTCHA verification failed."] });
            }
          } else {
              codes = verificationResponse.data.error-codes;
              // Handle the failed CAPTCHA verification
              res.render('index', { title: 'Bot-E', errors: [`CAPTCHA verification failed: ${codes}`] });
          }

      } catch (err) {
        // Handle error (e.g., API server might be down or there was a network error)
        res.render('index', { title: 'Bot-E', errors: ['There was an error sending the question to the API.'] });
      }
    }
});

module.exports = router;
