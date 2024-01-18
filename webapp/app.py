import os
import zipfile
import cv2
import base64
import io
import requests
import uuid
import numpy as np
import urllib.parse
import psycopg2

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, Response
from implement import draw_text_on_image, OCR
from PIL import Image, ImageGrab
from db import conn, cur, hasil_deteksi
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, 'D:/TA2023/webapp/static/upload')

hasil_deteksi()

db_params = {
    'database': 'plat_nomor',
    'user': 'postgres',
    'password': 'Sanyhasany0908',
    'host': 'localhost',
    'port': '5432',
}

@app.route('/')
def index():
    rows = get_data_from_db()
    return render_template('index.html', rows=rows)

def get_data_from_db():
    cur.execute("SELECT * FROM hasil_deteksi ORDER BY timestamp DESC")
    rows = cur.fetchall()
    return rows

#Fungsi untuk upload gambar
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        upload_file = request.files['image_name']
        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH, filename)
        upload_file.save(path_save)
        result = draw_text_on_image(path_save, filename)

        if result is None:
            result = 'Kosong'

        result_str = str(result)

        # Get the current timestamp
        timestamp = datetime.now()

        # Memasukkan data ke database
        with open(path_save, 'rb') as f:
            img_data = f.read()

        cur.execute("INSERT INTO hasil_deteksi(filename, hasil_pembacaan, timestamp) VALUES (%s, %s, %s)",
                    (filename, result_str, timestamp))
        conn.commit()

        return render_template('upload.html', upload=True, upload_image=filename, text=result_str)

    return render_template('upload.html', upload=False)

#camera feed
camera = cv2.VideoCapture(1)
def gen():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

#Untuk tangkap gambar
@app.route('/capture', methods=['POST', 'GET'])
def capture():
    if request.method == 'POST':
        ret, img = camera.read()
        filename = str(uuid.uuid1())[:4] + ".jpg"
        encoded_filename = urllib.parse.quote(filename)
        cv2.imwrite('D:/TA2023/webapp/static/capture/{}'.format(encoded_filename), img)
        result = draw_text_on_image('D:/TA2023/webapp/static/capture/{}'.format(encoded_filename), filename)
        if result is None:
            result = 'Kosong'

        result_str = str(result)

        # Get the current timestamp
        timestamp = datetime.now()

        cur.execute("INSERT INTO hasil_deteksi(filename, hasil_pembacaan, timestamp) VALUES (%s, %s, %s)",
                    (filename, result_str, timestamp))
        conn.commit()
        
        return render_template('image.html', filename=encoded_filename, text=result_str)
    else:
        return render_template('capture.html')
    
#Fungsi simpan dan pembacaan gambar
@app.route('/image/<filename>')
def image(filename):
    img_path = './webapp/static/capture/{}'.format(filename)
    img = cv2.imread(img_path)
    _, buffer = cv2.imencode('.jpg', img)
    img_data = base64.b64encode(buffer).decode()
    text = OCR(img_path, filename)
    
    return render_template('image.html', img_data=img_data, filename=filename, text=text)

#Fungsi menghapus gambar secara bersamaan
def delete_image_and_associated_files(filename):
    try:
        base_path = './webapp/static/capture/'
        image_path = os.path.join(base_path, filename)
        prediction_path = os.path.join('./webapp/static/predict/', filename)
        roi_path = os.path.join('./webapp/static/roi/', filename)
        result_path = os.path.join('./webapp/static/result/', filename)
        if os.path.exists(image_path):
            os.remove(image_path)
            if os.path.exists(prediction_path):
                os.remove(prediction_path)
            if os.path.exists(roi_path):
                os.remove(roi_path)
            if os.path.exists(result_path):
                os.remove(result_path)
            return redirect(url_for('capture'))
        else:
            return render_template('error.html', error='Image not found')
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/delete/<filename>', methods=['POST'])
def delete_image(filename):
    return delete_image_and_associated_files(filename)


if __name__ == "__main__":
    app.run(debug=True)