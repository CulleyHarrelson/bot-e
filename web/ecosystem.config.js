module.exports = {
  apps: [
    {
      name: 'bot-e.com',
      script: 'app.js',
      instances: 1,
      autorestart: true,
      //watch: process.env.NODE_ENV === 'development', 
      watch: true,
      env: {
        PORT: 3000, 
        DEBUG: '*', 
      },
      log_level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
    },
  ],
};
