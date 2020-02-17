"""
Main module of the server file
"""

# Local modules
from calories import config

# Get the application instance
connex_app = config.connex_app

# Read the swagger.yml.bak file to configure the endpoints
connex_app.add_api("swagger.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    connex_app.run(debug=True)
