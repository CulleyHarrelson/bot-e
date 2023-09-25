# Gunicorn configuration file

# Define the address and port to bind to
bind = "localhost:6464"  # Replace with your desired host and port

# Number of worker processes to spawn
workers = 4

# Specify the type of worker class
worker_class = "aiohttp.GunicornWebWorker"

# Maximum number of requests a worker will process before restarting
max_requests = 1000

# Maximum number of requests a worker will process before graceful shutdown
max_requests_jitter = 100

# Worker timeout in seconds (ensure it's greater than your application's timeout)
timeout = 30

# Log file location (optional)
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"

# Enable debugging mode (remove in production)
debug = False

# Set a custom process name (optional)
proc_name = "bot-e_gunicorn"

# Automatically reload workers when code changes (for development)
reload = False  # Set to True for development, but False for production
