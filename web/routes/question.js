var express = require('express');
var router = express.Router();
const axios = require('axios');

// Handle requests for /q/:question_id
router.get('/:question_id', function(req, res, next) {
  const questionId = req.params.question_id;

  axios.get(`http://localhost:6464/question/${questionId}`)
    .then(response => {
      const questionDetails = response.data; // Assuming the response contains the question details

      question = questionDetails[1];
      answer = JSON.parse(questionDetails[10]);
      answer = answer.replace(/\n/g, '<br>');


      // console.log("question details:", questionDetails[2]);
      res.render('question', { title: 'Question', questionId, question, answer });
    })
    .catch(error => {
      next(error); // Pass the error to the next middleware (error handler)
    });
});

module.exports = router;
