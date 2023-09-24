var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');
var axios = require('axios');  // <-- Require axios


/* POST home page. */
router.post('/', 
  [
    check('question_id', 'question_id is required').trim().isLength({ min: 1 }).escape(),
    //check('recaptcha_token', 'recaptcha_token is required').trim().isLength({ min: 1 }).escape()

  ],
  async (req, res) => {  // <-- Make the callback async
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      console.debug(errors)
      // There are errors. Render the form again with sanitized values and error messages.
      res.json({ success: false });
    }
    else {
      try {
        const question_id = req.body["question_id"];
        const enrich = req.body["enrich"];
        const apiServer = req.app.locals.apiServer;
        post_data = { question_id: question_id };
        if (enrich) {
          post_data['enrich'] = question_id
        }
        console.debug(post_data);
        const apiResponse = await axios.post(`${apiServer}/respond`, post_data);
        res.json({ success: true, question_id: apiResponse.data['question_id'] });
      } catch (err) {
        console.debug(err);
        res.json({ success: false });
      }

    }
});

module.exports = router;
