var express = require('express');
var router = express.Router();

router.get('/', function(req, res, next) {
  res.render('usage', { title: 'Usage Policies' });
});

module.exports = router;
