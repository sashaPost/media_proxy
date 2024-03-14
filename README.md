# Media Upload Service

This project provides a REST API for secure media file uploads, supporting images and documents.

## Features

*   Validates file types using MIME types and file extensions.
*   Checks uploaded file sizes against a configurable limit.
*   Saves uploaded files to designated directories (images/files).
*   Secures file paths and sets appropriate permissions.
*   API key authentication.

## Requirements
* Python 3.x 
* Flask
* python-docx
* Pillow (PIL Fork)
* python-magic

## Installation

1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt` 

## Usage

1. Set environment variables:
   ```bash
   export API_KEY=your_api_key
   export MEDIA_FILES_DEST=path/to/media/storage
