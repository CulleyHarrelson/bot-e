var express = require('express');
var router = express.Router();
const axios = require('axios');

router.get('/:search_for', function(req, res, next) {
  const search_for = req.params.search_for;
  axios.get(`http://localhost:6464/search/${search_for}`)
    .then(response => {
      const questionDetailsList = response.data; // Assuming the response contains a list of question details
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

      return res.render('search', { questions, search_for }); 
    })
    .catch(error => {
      next(error); // Pass the error to the next middleware (error handler)
    });
});

module.exports = router;
