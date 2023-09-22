module.exports = {
  apps: [
    {
      name: 'bot-e.com',
      script: 'app.js',
      instances: 1,
      autorestart: true,
      watch: process.env.BOTE_ENV === 'development', 
      env: {
        PORT: 3000, 
        DEBUG: '*', 
      },
      log_level: process.env.BOTE_ENV === 'development' ? 'debug' : 'info',
    },
  ],
};
