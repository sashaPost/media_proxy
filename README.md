# Media Proxy

## Description
Media Proxy is a Python-based application designed to manage and validate media files. It allows users to upload files and retrieve them through specified endpoints. The application is built using Flask and provides a simple interface for file management, including health checks to ensure the service is running correctly.
## Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#run-the-application)
- [Endpoints](#endpoints)
- [Testing and Code Quality](#testing-and-code-quality)
- [Contributing](#contributing)

## Requirements
* Python 3.10
* Docker

## Installation
1. Clone the repository<br>
`git clone https://github.com/sashaPost/media_proxy`<br>
`cd media_proxy`
2. Create a Virtual Environment: `python3 -m venv .venv`
3. Activate the Virtual Environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. In the root directory of the project, create a .env file and add your API key: `API_KEY="your_api_key"`

## Environment Variables
Set the following environment variables:
- FLASK_ENV: Set to development.
- FLASK_DEBUG: Set to 1.
- FLASK_HOST: Set to 0.0.0.0.
- FLASK_PORT: Set to 5000.

You can also set all necessary environment variables at once using the provided `set_env.sh` script:<br>
`chmod +x set_env.sh`<br>
`source ./set_env.sh`

## Running the Application
* Using Virtual Environment: `flask run`
* Using Docker
  - Build the Docker image: `docker build -t media_proxy .`
  - Run the container: `docker run -p 8080:5000 media_proxy`

## Endpoints
* Health Check Endpoint<br>
  You can check the health of the application by sending a request to the following endpoint:<br>
  `curl http://localhost:5000/health`
* Get Media File<br> Retrieve a file from the media directory:<br>`GET /media/<path:file_path>`<br>
  + Parameters:
    - `file_path` - The path to the requested file relative to the media directory.
  + Request Example:
    - `curl http://localhost:5000/media/images/file.jpg`
  + Success Response:<br>
    Returns the requested file.<br>
  + Error Response:<br>
    Returns a 404 error if the file is not found.<br>
    `{"error": "File not found"}`
* Upload Media File<br> Upload a file to the media directory:<br>`POST /media/<path:origin_file_path>`<br>
  + Parameters:
    - `origin_file_path` - The relative file path intended for the uploaded file.
  + Request Example:
    - `curl -X POST \`<br>
       `-H "Authorization: your_api_key" \`<br>
       `-F "file=@/path/to/your/upload_file.jpg" \`<br>
       `http://localhost:5000/media/images/upload_file.jpg`
  + Success Response:<br>
    Returns a message indicating success (200 OK).<br>
    `{"message": "OK"}`
  + Error Response:<br>
    Returns a 501 error if there was an issue during the upload process.<br>
    `{"error": "Error uploading file"}`

## Testing and Code Quality
* The project uses coverage for test `coverage` reporting.<br>
  Run tests with: `coverage run -m pytest`
* pre-commit is configured for managing `pre-commit` hooks to maintain code quality.

## Contributing
Feel free to contribute to the project by submitting issues or pull requests.
