#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
export FLASK_APP=app

echo "FLASK_ENV is set to: $FLASK_ENV"
echo "FLASK_DEBUG is set to: $FLASK_DEBUG"
echo "FLASK_HOST is set to: $FLASK_HOST"
echo "FLASK_PORT is set to: $FLASK_PORT"
echo "FLASK_APP is set to: $FLASK_APP"
