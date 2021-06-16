from flask import Flask, request, abort
from werkzeug.utils import secure_filename
import urllib
import urllib.request
import numpy as np
import cv2
import easyocr
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'easyocr_vdt');
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/data');
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

reader = easyocr.Reader(["ru","rs_cyrillic","be","bg","uk","mn","en"], gpu=False)

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS	

    
def url_to_image(url):
    """
    download the image, convert it to a NumPy array, and then read it into OpenCV format
    :param url: url to the image
    :return: image in format of Opencv
    """
    resp = urllib.request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    print("url = ", url)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image

def file_to_image(path):
    """
    convert local image to a NumPy array, and then read it into OpenCV format
    :param path: path to the image
    :return: image in format of Opencv
    """
    img = cv2.imread(path) 
    image = cv2.imdecode(img, cv2.IMREAD_COLOR)
    return image

def data_url_process(data):
    """
    read params from the received data from remote url
    :param data: in json format
    :return: params for image processing
    """    
    image_url = data["image_url"]
    secret_key = data["secret_key"]

    return url_to_image(image_url), secret_key

def data_file_process(data):	
    """
    Trying to extract image data from uploaded file
    """
    secret_key = data["secret_key"]
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
        return file_to_image(filename), secret_key
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


@app.route('/ocr', methods=['GET', 'POST'])
def processUrl():
    """
    received request from client and process the image
    :return: dict of width and points
    """
    data = request.get_json()
    image, secret_key = data_url_process(data)
    if secret_key == SECRET_KEY:
        results = recognition(image)
        return {
            "results": results
        }
    else:
        abort(401)

@app.route('/ocr_file', methods=['POST'])
def processFile():
    """
    received request from client and process the image (sent as file)
    :return: dict of width and points
    """
    data = request.get_json()
    image, secret_key = data_file_process(data)
    if secret_key == SECRET_KEY:
        results = recognition(image)
        return {
            "results": results
        }
    else:
        abort(401)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8200)
