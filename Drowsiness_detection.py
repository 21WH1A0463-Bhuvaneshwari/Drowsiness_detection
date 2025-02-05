from flask import Flask, render_template, Response
import cv2
from scipy.spatial import distance
from imutils import face_utils
import numpy as np
import pygame
import dlib

app = Flask(_name_)

video_capture = cv2.VideoCapture(0)


pygame.mixer.init()
pygame.mixer.music.load('audio/alert.wav')

EYE_ASPECT_RATIO_THRESHOLD = 0.3

EYE_ASPECT_RATIO_CONSEC_FRAMES = 50

COUNTER = 0

face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])

    ear = (A + B) / (2 * C)
    return ear

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(r"C:\Users\lasya\Downloads\shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS['left_eye']
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']

def generate_frames():
    while True:
        ret, frame = video_capture.read()

        if not ret or frame is None:
            continue  

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray, 0)

        face_rectangle = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in face_rectangle:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        for face in faces:
            shape = predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]

            leftEyeAspectRatio = eye_aspect_ratio(leftEye)
            rightEyeAspectRatio = eye_aspect_ratio(rightEye)

            eyeAspectRatio = (leftEyeAspectRatio + rightEyeAspectRatio) / 2

            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            if eyeAspectRatio < EYE_ASPECT_RATIO_THRESHOLD:
                COUNTER += 1

                if COUNTER >= EYE_ASPECT_RATIO_CONSEC_FRAMES:
                    pygame.mixer.music.play(-1)
                    cv2.putText(frame, "You are Drowsy", (150, 200), cv2.FONT_HERSHEY_TRIPLEX, 1.5, (128, 0, 0), 2)
            else:
                pygame.mixer.music.stop()
                COUNTER = 0

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if _name_ == "_main_":
    app.run(debug=True)
    
body {
    background-color: rgb(0, 128, 94);
}

h1 {
    text-align: center;
    color: white; /* Change text color to white for better visibility */
}

.video-feed {
    display: block;
    margin: 0 auto;
    border: 5px solid #FFEFEF;
    background-color: white; /* Add a white background to the video feed container */
}<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Drowsiness Detection</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h1>Drowsiness Detection</h1>
    
    <img src="{{ url_for('video_feed') }}" class="video-feed" alt="Video Feed">
</body>
</html>
