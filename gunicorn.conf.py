# gunicorn.conf.py
import platform

# Determine the operating system
is_freebsd = platform.system() == "FreeBSD"

# Define the Gunicorn configuration
bind = "localhost:6464"  # Bind to the specified host and port
worker_class = "aiohttp.GunicornWebWorker"  # Use aiohttp worker class
accesslog = "log/api_access.log"  # Specify the access log file
errorlog = "log/api_error.log"  # Specify the error log file

# Set the log level based on the operating system
if is_freebsd:
    loglevel = "info"  # Use a suitable log level for production on FreeBSD
else:
    loglevel = "debug"  # Use a debug log level for other operating systems

daemon = True  # Run Gunicorn in daemon mode

# Conditionally set reload based on the operating system
reload = not is_freebsd  # Set to True for non-FreeBSD systems
