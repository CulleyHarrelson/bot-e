#!/usr/bin/env bash

gunicorn api:app --worker-class aiohttp.GunicornWebWorker --bind localhost:6464 --access-logfile - --error-logfile - --reload
#gunicorn api:app --worker-class aiohttp.GunicornWebWorker --bind localhost:6464 --reload --access-logfile logs/api_access.log --error-logfile logs/api_error.log --log-level debug

