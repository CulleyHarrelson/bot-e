var express = require('express');
var router = express.Router();
const axios = require('axios');
var http = require('http');


// Handle requests for /q/:question_id
router.get('/:question_id', function(req, res, next) {
  // console.log("session_id:", req.sessionID);
  const questionId = req.params.question_id;
  const sessionId = req.sessionID; 
  axios.get(`http://localhost:6464/question/${questionId}`)
    .then(response => {
      const questionDetails = response.data; // Assuming the response contains the question details
      description = questionDetails['description']
      question_id = questionDetails['question_id']

      try {
        title = questionDetails['title']
        title = title.replace(/"/g, '');
      } catch (error) {
        title = 'Question:'
      }
      image_url = questionDetails['image_url']
      media = questionDetails['media']

      try {
        question = JSON.parse(questionDetails['question']);
        question = question.replace(/\n/g, '<p>');
      } catch (error) {
        question = questionDetails['question'];
        try {
          question = question.replace(/\n/g, '<p>');
        } catch (error) {
          pass
        }
      }
      try {
        answer = JSON.parse(questionDetails['answer']);
        answer = answer.replace(/\n/g, '<p>');
      } catch (error) {
        answer = null;
      }

      const canonical = "https://bot-e.com/question/" + questionId

      // console.log("question details:", questionDetails[2]);
      return res.render('question', { title, questionId, question, answer, sessionId, canonical });
    })
    .catch(error => {
      next(error); // Pass the error to the next middleware (error handler)
    });
});

module.exports = router;
