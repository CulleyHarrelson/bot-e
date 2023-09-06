var createError = require('http-errors');
var express = require('express');
var session = require('express-session');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');

var indexRouter = require('./routes/index');
var tosRouter = require('./routes/tos');
var aboutRouter = require('./routes/about');
var questionRouter = require('./routes/question');
var searchRouter = require('./routes/search');

var app = express();

const sess = {
  secret: 'keyboard cat',
  resave: false, // Set to false to avoid the deprecated warning
  saveUninitialized: true, // Set to true or false as needed
  cookie: {}
};

if (app.get('env') === 'production') {
  app.set('trust proxy', 1); // trust first proxy
  sess.cookie.secure = true; // serve secure cookies
}

app.use(session(sess));

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');
//if (app.get('env') === 'development') {
app.locals.pretty = true;
//}

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', indexRouter);
app.use('/tos', tosRouter);
app.use('/question', questionRouter);
app.use('/about', aboutRouter);
app.use('/search', searchRouter);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;

// this is here until it finds a better place
function generateRandomKey() {
  const length = 11;
  const chars = '-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  let key = '';

  // Generate the first character
  const randomIndex = Math.floor(Math.random() * (chars.length - 2)) + 2; // Exclude "_" and "-" from the first character
  key += chars.charAt(randomIndex);

  // Generate the rest of the characters
  for (let i = 1; i < length - 1; i++) {
    const randomIndex = Math.floor(Math.random() * chars.length);
    key += chars.charAt(randomIndex);
  }

  // Generate the last character
  const randomIndexLast = Math.floor(Math.random() * (chars.length - 2)) + 2; // Exclude "_" and "-" from the last character
  key += chars.charAt(randomIndexLast);

  return key;
}
