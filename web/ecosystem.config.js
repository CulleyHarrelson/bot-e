module.exports = {
  apps: [
    {
      name: 'bot-e.com',
      script: 'app.js',
      instances: 1,
      autorestart: true,
      watch: process.env.BOTE_ENV === 'development', 
      watch: true,
      env: {
        PORT: 3000, 
        DEBUG: '*', 
      },
      log_level: process.env.BOTE_ENV === 'development' ? 'debug' : 'info',
      error_file: `${process.env.BOTE_PATH}/logs/pm2_error.log`,
      out_file: `${process.env.BOTE_PATH}/logs/pm2_output.log`,
    },
  ],
};
