import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug import secure_filename
import keras
import numpy as np
from keras.models import Sequential,load_model
from PIL import Image
import keras
import sys
import numpy as np
import tensorflow as tf
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
classes = ["monkey","boar","crow"]
num_classes = len(classes)
image_size = 50
model = load_model("./animal_cnn.h5")
graph = tf.get_default_graph()


app = Flask(__name__)

app.secret_key = 'super secret string'
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_NATIVE_UNICODE'] = 'utf-8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),unique=True)
    password = db.Column(db.String(80),unique=True)

    def __init__(self, username, password=None):
        self.username = username
        self.password = password
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
@app.route('/')
def index():
    user_list = User.query.all()
    if 'username' in session:
        return render_template('index.html',user_list=user_list)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'kei':
            session['username'] = request.form['username']
            session['password'] = request.form['password']
            return redirect(url_for('index'))
        else:
            return '''<p>ユーザー名が違います</p>'''
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        img_file = request.files['img_file']
        if img_file and allowed_file(img_file.filename):
            filename = secure_filename(img_file.filename)
            img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = '/uploads/' + filename

            filepath = os.path.join(app.config["UPLOAD_FOLDER"],filename)


            image = Image.open(filepath)
            image = image.convert("RGB")
            image = image.resize((image_size,image_size))
            data = np.asarray(image)
            X=[]
            X.append(data)
            X = np.array(X)
            global graph
            with graph.as_default():
                result = model.predict([X])[0]
                predicted = result.argmax()
                percentage = int(result[predicted]*100)
                result_str = "ラベル"+classes[predicted]+"確率" + str(percentage) + '%'
                return render_template('index.html', img_url=img_url,result_str=result_str)
        else:
            return ''' <p>許可されていない拡張子です</p> '''
    else:
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__ == '__main__':
    app.debug = True
    app.run()
