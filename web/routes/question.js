var express = require('express');
var router = express.Router();
const axios = require('axios');

// Handle requests for /q/:question_id
router.get('/:question_id', function(req, res, next) {
  const questionId = req.params.question_id;

  axios.get(`http://localhost:6464/ask/${questionId}`)
    .then(response => {
      const questionDetails = response.data; // Assuming the response contains the question details

      //console.log("question details:", questionDetails);
      try {
        question = JSON.parse(questionDetails['question']);
        question = question.replace(/\n/g, '<p>');
      } catch (error) {
        question = questionDetails['question'];
        // question = question.replace(/\n/g, '<p class="lead">');
      }
      try {
        answer = JSON.parse(questionDetails['answer']);
        answer = answer.replace(/\n/g, '<p>');
      } catch (error) {
        answer = null;
      }


      // console.log("question details:", questionDetails[2]);
      res.render('question', { title: 'bot-e', questionId, question, answer });
    })
    .catch(error => {
      next(error); // Pass the error to the next middleware (error handler)
    });
});

module.exports = router;
