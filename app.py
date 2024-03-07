from flask import Flask, Response, request
import imghdr   # Determine the type of an image
from werkzeug.utils import secure_filename
import os
import secrets
import logging
# from dotenv import load_dotenv

# the second approach:
# from flask_uploads import UploadSet, configure_uploads, IMAGES
# photos = UploadSet('photos', IMAGES)

# load_dotenv() 

app = Flask(__name__)
app.config["SECRET_KEY"] = str(secrets.SystemRandom().getrandbits(128))
# https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024    # Limit file size to 24MB
app.config['UPLOAD_EXTENSIONS'] = ['jpeg', 'jpg', 'png', 'gif']
app.config['UPLOADED_IMAGES_DEST'] = 'media/images'
app.config['ENV'] = 'production'
app.config['DEBUG'] = False 

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('HTTPS_Request')

# backend_hostname = os.getenv("BACKEND_HOSTNAME")

# def validate_image(file_name):
#     image_type = imghdr.what(file_name)
#     if image_type:
#         return True
#     return False    

# was replaced by 'validate_image()'
def allowed_file(file_name):
    # DEBUG:
    # file_extension = filename.rsplit('.', 1)[1].lower()
    # print(f"Extracted file extension: {file_extension}")
    return '.' in file_name and file_name.rsplit('.', 1)[1].lower() in app.config['UPLOAD_EXTENSIONS']

@app.route('/media/images/<filename>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(filename):
    # DEBUG:
    # print(request)
    if request.method == 'GET':
        file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
        # DEBUG:
        # print(f"File Path: {file_path}")
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
            return Response(content, mimetype='application/octet-stream')
        except FileNotFoundError:
            # DEBUG:
            # print("File not found")
            return Response("File not found", status=404)
        except Exception as e:
            # DEBUG:
            # print(f"Error: {str(e)}")
            # return Response(f"Error: {str(e)}", status=500)
            return Response("Error: {}".format(str(e)), status=500)
                
    elif request.method == 'POST':
        
        logger.info(f'HOST: {request.host}')
        # logger.info(f'BACK (env): {backend_hostname}')
        client_hostname = request.remote_addr
        logger.info(f'Client Hostname: {client_hostname}')
        # if client_hostname != 'HuIet4':
        if client_hostname != '192.168.1.2':
            return Response("FUCK OFF", status=403)
    
        if 'file' not in request.files:
            return Response("No file part", status=400)

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return Response("No selected file", status=400)
        
        if not allowed_file(uploaded_file.filename):
            return Response("File type not allowed", status=400)
        else:
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
            uploaded_file.save(file_path)
            os.chmod(file_path, 0o775)
            return Response("File was uploaded successfully", status=200)

        # validate_image() duplicates allowed_file()
        # if validate_image(uploaded_file.filename):             
        #     filename = secure_filename(uploaded_file.filename)
        #     file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
        #     uploaded_file.save(file_path)
        #     return Response("File was uploaded successfully", status=200)
        # else:
        #     return Response("Not an image file", status=400)
        
    elif request.method == 'PUT':
        file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
        # DEBUG:
        # print(file_path)
        if not os.path.exists(file_path):
            return Response("File does not exist", status=404)
        
        if 'file' not in request.files:
            return Response("No file part", status=400)

        uploaded_file = request.files['file']
        # DEBUG:
        # print(uploaded_file)
        if uploaded_file.filename == '':
            return Response("No selected file", status=400)
        
        if not allowed_file(uploaded_file.filename):
            return Response("File type not allowed", status=400)
        else:
            uploaded_filename = secure_filename(uploaded_file.filename)
            uploaded_file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], uploaded_filename) 
            # Remove the old file and replace it with the new one
            os.remove(file_path)
            uploaded_file.save(uploaded_file_path)
            # DEBUG:
            # print(file_path)
            os.rename(uploaded_file_path, file_path)
            return Response("File was updated successfully", status=200)

        # # validate_image() duplicates allowed_file()
        # if validate_image(uploaded_file.filename):             
        #     uploaded_filename = secure_filename(uploaded_file.filename)
        #     uploaded_file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], uploaded_filename) 
        #     # Remove the old file and replace it with the new one
        #     os.remove(file_path)
        #     uploaded_file.save(uploaded_file_path)
        #     # DEBUG:
        #     # print(file_path)
        #     os.rename(uploaded_file_path, file_path)
        #     return Response("File was updated successfully", status=200)
        # else:
        #     return Response("Not an image file", status=400)

    elif request.method == 'DELETE':
        file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)  # Remove the file
            return Response("File was deleted successfully", status=200)
        else:
            return Response("File not found", status=404)
    return Response("Unsupported method", status=405)



if __name__ == '__main__':
    app.run()

# # media/images/zystrich3.jpg
# @app.route('/test', methods=['GET'])
# def test():
#     filename = 'zystrich3.jpg'
#     file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
#     print(file_path)
#     with open(file_path, 'rb') as file:
#         content = file.read()
#     return Response(content, mimetype='application/octet-stream')
