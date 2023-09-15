var express = require('express');
var router = express.Router();
const axios = require('axios');

router.get('/:start_date', function(req, res, next) {
  const start_date = req.params.start_date;
  const apiServer = req.app.locals.apiServer;
  axios.get(`${apiServer}/trending/${start_date}`)
    .then(response => {
      const questionDetailsList = response.data; 
      const questions = [];

      for (const questionDetails of questionDetailsList) {
        const title = questionDetails['title'].replace(/"/g, '');
        const description = questionDetails['description'];
        const image_url = questionDetails['image_url'];
        const media = questionDetails['media'];
        const question_id = questionDetails['question_id'];

        let question = questionDetails['question'];
        try {
          question = JSON.parse(question).replace(/\n/g, '<p>');
        } catch (error) {
          question = question.replace(/\n/g, '<p>');
        }

        let answer = questionDetails['answer'];
        try {
          answer = JSON.parse(answer).replace(/\n/g, '<p>');
        } catch (error) {
          answer = null;
        }

        const canonical = "/question/" + question_id;

        questions.push({ title, description, image_url, media, question, answer, canonical });
      }

      return res.render('trending', { questions, start_date }); 
    })
    .catch(error => {
      if (error.response && error.response.data && error.response.data.error) {
        // The error message from the Flask API is available in error.response.data.error
        const errorMessage = error.response.data.error;
        // Handle the error or send it to the error handler
        next(new Error(errorMessage));
      } else {
        // Handle other Axios or network errors
        next(error);
      }
    });
});

module.exports = router;
