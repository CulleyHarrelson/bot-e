var express = require('express');
var router = express.Router();

// Handle requests for /q/:question_id
router.get('/:question_id', function(req, res, next) {
  const questionId = req.params.question_id;

  // Fetch question details using questionId
  // Replace the following line with your logic to fetch question details
  // const questionDetails = getQuestionDetails(questionId);

  res.render('question', { title: 'Question', questionId });
});

module.exports = router;
