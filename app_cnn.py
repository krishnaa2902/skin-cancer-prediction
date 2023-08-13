from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import numpy as np
from PIL import Image
import tensorflow as tf

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

#models
model = tf.keras.models.load_model('model2.h5')
model2 = tf.keras.models.load_model('resnetmodel.h5')
model3 = tf.keras.models.load_model('skin_cancer_inceptionv3.h5')

#class names
class_names = ['malignant', 'benign']

DB_NAME = 'database.db'



@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        mobile = request.form['mobile']
        blood_group = request.form['blood_group']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO patients (name, age, gender, mobile, blood_group) VALUES (?, ?, ?, ?, ?)',
            (name, age, gender, mobile,blood_group)
        )
        patient_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO users (email, username, password, patient_id) VALUES (?, ?, ?, ?)',
            (email, username, password, patient_id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:
            session['user_id'] = user[0]
            # return redirect(url_for('profile'))
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        if request.method == 'POST':
            # Get the uploaded image file
            file = request.files['file']
            
            # Open and preprocess the image
            #CNN MODEL
            print("CNN MODEL")
            img = Image.open(file)
            image = img.resize((150, 150))
            image = np.array(image) / 255.0
            image = np.expand_dims(image, axis=0)
            # Make the prediction
            prediction = model.predict(image)
            print(prediction)
            if(prediction[0]>0.5):
                predicted_class = 1
            else:
                predicted_class = 0
            predicted_label = class_names[predicted_class]

            #RESNET MODEL
            print("RESNET MODEL")
            image1 = img.resize((224, 224))  
            image1 = np.array(image1) / 255.0  
            image1 = np.expand_dims(image1, axis=0)
            prediction1 = model2.predict(image1)
            if(prediction1[0][0]>prediction1[0][1]):
                print("malignant")
                predicted_class1=0
            else:
                print("benign")
                predicted_class1=1
            print(predicted_class1)
            # Display the predicted class
            predicted_label1 = class_names[predicted_class1]

            
            #INCEPTIONV3 MODEL
            print("INCEPTION V3 MODEL")
            image2 = img.resize((75, 75))  
            image2 = np.array(image2) / 255.0
            image2 = np.expand_dims(image2, axis=0)
            prediction2 = model3.predict(image2)
            if(prediction2[0][0]>prediction2[0][1]):
                print("malignant")
                predicted_class2=0
            else:
                print("benign")
                predicted_class2=1
            print(predicted_class2)
            # Display the predicted class
            predicted_label2 = class_names[predicted_class2]
            # Render the result page with the prediction
            return render_template('result.html', predicted_label=predicted_label,predicted_label1=predicted_label1,predicted_label2=predicted_label2)
        
        return render_template('index1.html')

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users JOIN patients ON users.patient_id = patients.id WHERE users.id = ?',
                       (user_id,))
        user = cursor.fetchone()
        # for row in user:
        #     print(row)
        conn.close()

        if user:
            return render_template('profile.html', user=user)

    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



    
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    mobile TEXT NOT NULL,
    blood_group TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    patient_id INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''') 
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
app.run(debug=True)
