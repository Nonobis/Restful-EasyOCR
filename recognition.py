from flask import Flask, request, abort
import os 
import logging
import ast
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import numpy as np
import cv2
import easyocr
import os

SERVER_HOST=os.getenv('SERVER_HOST','0.0.0.0');
SERVER_PORT = os.getenv('SERVER_PORT', '8200');
SECRET_KEY = os.getenv('SECRET_KEY', '7pK68LHhWwW7AP');

# Max 16M Upload for file
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# Minimal acceptance score
MIN_SCORE = os.getenv('MIN_SCORE', '');

# determine if we use GPU
raw = os.getenv('USE_GPU', 'false').title();
USE_GPU = ast.literal_eval(raw);

# Instance OCR Reader
reader = easyocr.Reader(["en"], gpu=USE_GPU)

# Instance Flask
app = Flask(__name__)

# Instance Logger
logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
handler = logging.FileHandler('EasyOCR.log') # creates handler for the log file
logger.addHandler(handler) # adds handler to the werkzeug WSGI logger

# Create local upload path
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
	
	# convert to grayscale
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	
	# only take image center
        center_cropped = center_crop(gray)
	
        return center_cropped
    else:
        app.logger.error("Failed to read image")
        abort(401)

def center_crop(img, new_width=None, new_height=None):        

    width = img.shape[1]
    height = img.shape[0]

    if new_width is None:
        new_width = min(width, height)

    if new_height is None:
        new_height = min(width, height)

    left = int(np.ceil((width - new_width) / 2))
    right = width - floor((width - new_width) / 2)

    top = int(np.ceil((height - new_height) / 2))
    bottom = height - int(np.floor((height - new_height) / 2))

    if len(img.shape) == 2:
        center_cropped_img = img[top:bottom, left:right]
    else:
        center_cropped_img = img[top:bottom, left:right, ...]

    return center_cropped_img

def data_file_process(data):	
    """
    Trying to extract image data from uploaded file
    """
    secret_key = data.form.get('secret_key')
    
    if request.method == 'POST':		
     # check if the post request has the file part
     if 'file' not in request.files:
        app.logger.error('No file part')	  
        abort(401)

     file = request.files['file']	
     if file.filename == '':
        app.logger.error('No image selected for uploading') 
        abort(401)
	
     if file and allowed_file(file.filename):
        app.logger.info('image ' + filename + ' format is allowed.') 
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        app.logger.info('upload_image filename: ' + filename)
        return file_to_image(os.path.join(app.config['UPLOAD_FOLDER'], filename)), secret_key
     else:
        app.logger.error('Allowed image types are -> png, jpg, jpeg, gif') 
        abort(401)


def recognition(image, min_score):
    """

    :param image:
    :return:
    """
    results = []
    texts = reader.readtext(image)
    for (bbox, text, prob) in texts:
	if ( min_score == '' || prob>float(min_score)):
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
        results = recognition(image, MIN_SCORE)
        return {
            "results": results
        }
    else:
        app.logger.error('Secret Key is invalid.') 
	

if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT)
