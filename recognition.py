from flask import Flask, request, abort
import os      
import ast
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import numpy as np
import cv2
import easyocr
import os

SECRET_KEY = os.getenv('SECRET_KEY', '7pK68LHhWwW7AP');
USE_GPU = getenv_bool('USE_GPU');
SERVER_HOST=os.getenv('SERVER_HOST','0.0.0.0');
SERVER_PORT = os.getenv('SERVER_PORT', '8200');

reader = easyocr.Reader(["ru","rs_cyrillic","be","bg","uk","mn","en"], gpu=USE_GPU)

app = Flask(__name__)

#It will allow below 16MB contents only, you can change it
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

path = os.getcwd()
defaultFolder = os.path.join(path, '/data');
isdir = os.path.isdir(defaultFolder) 
if not os.path.isdir(defaultFolder):
    os.mkdir(defaultFolder);

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', defaultFolder);
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def getenv_bool(name: str, default: str = "False"):
    raw = os.getenv(name, default).title()
    return ast.literal_eval(raw)

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS	

def file_to_image(path):
    """
    convert local image to a NumPy array, and then read it into OpenCV format
    :param path: path to the image
    :return: image in format of Opencv
    """
    if os.path.isfile(path):
        
        #read the data from the file
        with open(path, 'rb') as infile:
            buf = infile.read()
     
        #use numpy to construct an array from the bytes
        x = np.fromstring(buf, dtype='uint8')

        #decode the array into an image
        image = cv2.imdecode(x, cv2.IMREAD_UNCHANGED)
        return image
    else:
        print("Failed to read image")
        abort(401)

def data_file_process(data):	
    """
    Trying to extract image data from uploaded file
    """
    secret_key = data.form.get('secret_key')
    
    if request.method == 'POST':		
     # check if the post request has the file part
     if 'file' not in request.files:
        print('No file part')	  
        abort(401)

     file = request.files['file']	
     if file.filename == '':
        print('No image selected for uploading') 
        abort(401)
	
     if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print('upload_image filename: ' + filename)
        return file_to_image(os.path.join(app.config['UPLOAD_FOLDER'], filename)), secret_key
     else:
        print('Allowed image types are -> png, jpg, jpeg, gif') 
        abort(401)


def recognition(image):
    """

    :param image:
    :return:
    """
    results = []
    texts = reader.readtext(image)
    for (bbox, text, prob) in texts:
        output = {
            "coordinate": [list(map(float, coordinate)) for coordinate in bbox],
            "text": text,
            "score": prob
        }
        results.append(output)

    return results

@app.route('/ocr_file', methods=['POST'])
def processFile():
    """
    received request from client and process the image (sent as file)
    :return: dict of width and points
    """
    image, secret_key = data_file_process(request)
    if secret_key == SECRET_KEY:
        results = recognition(image)
        return {
            "results": results
        }

if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT)
