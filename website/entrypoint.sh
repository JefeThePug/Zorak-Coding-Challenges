#!/bin/bash
# This script runs when the api container starts up.
python setup.py ${DISCORD_ADMIN_USER_ID} && python app.py