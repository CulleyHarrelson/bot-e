var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');
var axios = require('axios');  // <-- Require axios

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'bot-e', description: 'bot-e: advice column 2.0.  What\'s going on?', canonical: 'https://bot-e/' });
});

/* POST home page. */
router.post('/', 
  [
    // Validate and sanitize the 'question' field.
    check('question', 'question is required').trim().isLength({ min: 1 }).escape()
  ],
  async (req, res) => {  // <-- Make the callback async
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // There are errors. Render the form again with sanitized values and error messages.
      res.render('index', { title: 'bot-e', errors: errors.array() });
    }
    else {
      try {
        // Post the question to the local API server and store the result.

        const apiResponse = await axios.post('http://127.0.0.1:6464/ask', { question: req.body.question });
        // console.log("after");
        //console.log("api response:", apiResponse.data['question_id']);


        res.redirect("/question/" + apiResponse.data['question_id']);
         

        // The form data is valid. Include the API response in the rendered view.
        // salkdfj
        //res.render('index', { 
        //    title: 'bot-e', 
        //    question: apiResponse.data[0]
        //});
      } catch (err) {
        // Handle error (e.g., API server might be down or there was a network error)
        res.render('index', { title: 'bot-e', errors: [{msg: 'There was an error sending the question to the API.'}] });
      }
    }
});

module.exports = router;
