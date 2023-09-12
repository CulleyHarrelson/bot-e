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
var captchaRouter = require('./routes/recaptcha');
var navigateRouter = require('./routes/navigate');
var trendingRouter = require('./routes/trending');
var commentRouter = require('./routes/comment');

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
app.use('/recaptcha', captchaRouter);
app.use('/navigate', navigateRouter);
app.use('/trending', trendingRouter);
app.use('/comment', commentRouter);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // Log the error to your console
  //console.error('Error:', err);

  // Set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  let axiosErrorMessage = ''; // Initialize axiosErrorMessage variable

  // Check if the error is an Axios error and contains a response
  if (err.isAxiosError && err.response) {
    // Access the error message from the Axios error response
    axiosErrorMessage = err.response.data.error;
    console.error('Axios Error Message:', axiosErrorMessage);
  }

  // Render the error page with axiosErrorMessage as a variable
  res.status(err.status || 500);
  res.render('error', { axiosErrorMessage }); // Pass axiosErrorMessage to the template
});

module.exports = app;
