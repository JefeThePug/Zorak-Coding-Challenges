#!/bin/bash
# This script runs when the api container starts up.

python setup.py "${DISCORD_ADMIN_USER_ID}"

# Replace 'your_module:app' with the actual path to your Flask app instance
exec gunicorn --bind 0.0.0.0:5000 app:app