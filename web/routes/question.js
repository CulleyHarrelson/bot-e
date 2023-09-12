const express = require('express');
const router = express.Router();
const axios = require('axios');

// Handle requests for /q/:question_id
router.get('/:question_id', async function(req, res, next) {
  try {
    const questionId = req.params.question_id;
    const sessionId = req.sessionID;

    // Make the first request to get question details
    const questionDetailsResponse = await axios.get(`http://localhost:6464/question/${questionId}`);
    const questionDetails = questionDetailsResponse.data; // Assuming the response contains the question details

    // Make the second request to get comments data
    const commentsResponse = await axios.get(`http://localhost:6464/comments/${questionId}`);
    const comments = commentsResponse.data; // Assuming the response contains comments data

    // Process and format the data as needed
    const title = questionDetails.title ? questionDetails.title.replace(/"/g, '') : 'Question:';
    const description = questionDetails.description;
    const image_url = questionDetails.image_url;
    const media = questionDetails.media;

    let question = questionDetails.question;
    if (question) {
      try {
        question = JSON.parse(question).replace(/\n/g, '<p>');
      } catch (error) {
        question = question.replace(/\n/g, '<p>');
      }
    }

    let answer = questionDetails.answer;
    if (answer) {
      try {
        answer = JSON.parse(answer).replace(/\n/g, '<p>');
      } catch (error) {
        answer = null;
      }
    }

    const canonical = `https://bot-e.com/question/${questionId}`;

    // Combine the question and comments data into a single object
    const responseData = {
      title,
      questionId,
      question,
      answer,
      image_url,
      sessionId,
      canonical,
      comments, // Include comments data
    };

    // Render your template and pass the combined data
    res.render('question', responseData);
  } catch (error) {
    next(error); // Pass any errors to the next middleware (error handler)
  }
});

module.exports = router;
