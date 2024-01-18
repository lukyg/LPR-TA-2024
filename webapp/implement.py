import os
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
import imutils
import easyocr
import plotly.express as px
import matplotlib.pyplot as plt
import xml.etree.ElementTree as xet
import tensorflow as tf

from glob import glob
from skimage import io
from shutil import copy
from tensorflow.python.keras.models import Model
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense, Conv2D, MaxPool2D , Flatten
from tensorflow.python.keras.layers import Dense, Dropout, Flatten, Input
from PIL import Image
from matplotlib import pyplot as plt

model = tf.keras.models.load_model('D:/TA2023/model/LPR_VGG16_050124_Sigmoid')

def object_detection(path, filename):
    
    #Pembacaan gambar
    image = tf.keras.preprocessing.image.load_img(path) # PIL object
    image = np.array(image,dtype=np.uint8) # 8 bit array (0,255)
    image1 = tf.keras.preprocessing.image.load_img(path,target_size=(256,256))
    
    # Data preprocessing
    image_arr_224 = tf.keras.preprocessing.image.img_to_array(image1)/255.0 # Convert to array & normalized
    h,w,d = image.shape
    test_arr = image_arr_224.reshape(1,256,256,3)
    
    #Prediksi
    coords = model.predict(test_arr)
    
    # Denormalisasi nilai array
    denorm = np.array([w,w,h,h])
    coords = coords * denorm
    coords = coords.astype(np.int32)
    
    #membuat boundbox berdasarkan nilai denorm prediksi
    xmin, xmax,ymin,ymax = coords[0]
    pt1 =(xmin,ymin)
    pt2 =(xmax,ymax)
    print(pt1, pt2)
    cv2.rectangle(image,pt1,pt2,(0, 0, 255),3)
    
    #convert ke RGB
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite('./webapp/static/predict/{}'.format(filename), image_bgr)
    return coords

def OCR(path, filename):
    img = np.array(tf.keras.preprocessing.image.load_img(path))
    coords = object_detection(path, filename)
    xmin ,xmax,ymin,ymax = coords[0]
    roi = img[ymin:ymax,xmin:xmax]
    roi_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
    cv2.imwrite('./webapp/static/roi/{}'.format(filename), roi_bgr)
    reader = easyocr.Reader(['en'])
    result = reader.readtext(roi, detail=0, paragraph=True)
    print(result)
    return result

def draw_text_on_image(path, filename):
    #pengambilan text dan nilai dari bounding box hasil prediksi
    result1 = OCR(path, filename)
    img = np.array(tf.keras.preprocessing.image.load_img(path))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    coords = object_detection(path, filename)
    xmin, xmax, ymin, ymax = coords[0]
    pt1 = (xmin, ymin)
    pt2 = (xmax, ymax)

    #menggambar bounding box
    img = cv2.rectangle(img, pt1, pt2, (0, 0, 255), 3)

    #Menyatukan setiap karakter dari text yang terbaca
    text = ' '.join(result1)

    #membuat frame untuk text yang terbaca
    if text:
        lw = max(round(sum(img.shape) / 2 * 0.003), 2)
        w, h = cv2.getTextSize(text, 0, fontScale=lw / 3, thickness=max(lw - 1, 1))[0]
        outside = pt1[1] - h >= 3
        p2 = pt1[0] + w, pt1[1] - h - 3 if outside else pt1[1] + h + 3
        cv2.rectangle(img, pt1, p2, (0, 0, 255), -1, cv2.LINE_AA)  # filled
        cv2.putText(img, text, (pt1[0], pt1[1] - 2 if outside else pt1[1] + h + 2),
                    0, lw / 3, (255, 255, 255), thickness=max(lw - 1, 1), lineType=cv2.LINE_AA)

    #Menyimpan hasil
    cv2.imwrite('./webapp/static/result/{}'.format(filename), img)

    return result1