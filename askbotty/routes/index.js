var express = require('express');
var router = express.Router();
var { check, validationResult } = require('express-validator');

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Ask Botty' });
});

/* POST home page. */
router.post('/', 
  [
    // Validate and sanitize the 'message' field.
    check('message', 'Message is required').trim().isLength({ min: 1 }).escape()
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // There are errors. Render the form again with sanitized values and error messages.
      res.render('index', { title: 'Ask Botty', errors: errors.array() });
    }
    else {
      // The form data is valid.
      res.render('index', { title: 'Ask Botty', message: req.body.message });
    }
});

module.exports = router;

