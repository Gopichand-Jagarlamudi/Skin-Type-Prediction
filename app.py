import os
import sqlite3
from flask import Flask, redirect, render_template, request, session, flash, url_for

from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime 

import tensorflow as tf
import numpy as np
model = tf.keras.models.load_model('static/XCE.h5')
from tensorflow.keras.preprocessing import image
from PIL import Image
import torchvision.transforms.functional as TF
import CNN

import torch
import pandas as pd
import csv

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# --- Initialize SQLite Database ---
DATABASE = 'users.db'

supplement_info = pd.read_csv('media/supplement_info.csv', encoding='cp1252')
emstore_info = pd.read_csv('media/emstore.csv')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# --- Helper: Get DB Connection ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dict-like access
    return conn

# --- Routes ---

@app.route('/')
def intro_page():
    if 'user' in session:
        return redirect(url_for('home_page'))
    return render_template('intro.html')

@app.route('/home')
def home_page():
    user = session.get('user')
    if user!=None:
        return render_template('home.html', user=user)
    else:
        return render_template(
            'alert_redirect.html',
            message="⛔ Please log in to access this feature!",
            redirect_url=url_for('login')
        ), 403
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']  # Store name in session
            session['email'] = user['email']
            flash('🎉 Login successful! Welcome back.', 'success')
            return redirect(url_for('home_page'))
        else:
            flash('❌ Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate passwords match
        if password != confirm_password:
            flash('⚠️ Passwords do not match.', 'warning')
            return render_template('register.html')

        # Check if email exists
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if existing_user:
            conn.close()
            flash('⚠️ Email already registered.', 'warning')
            return render_template('register.html')

        # Insert new user
        hashed_pw = generate_password_hash(password)
        conn.execute('''
            INSERT INTO users (name, age, gender, email, phone, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, age, gender, email, phone, hashed_pw))
        conn.commit()
        conn.close()

        flash('✅ Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('email', None)
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('intro_page'))

# --- Other Routes (unchanged) ---
@app.route('/contact')
def contact():
    return render_template('contact-us.html', user=session.get('user'))

@app.route('/index')
def ai_engine_page():
    user = session.get('user')
    if user!=None:
        return render_template('index.html', user=session.get('user'))
    else:
        return render_template(
            'alert_redirect.html',
            message="⛔ Please log in to access this feature!",
            redirect_url=url_for('login')
        ), 403
@app.route('/mobile-device')
def mobile_device_detected_page():
    return render_template('mobile-device.html', user=session.get('user'))

@app.route('/submit222', methods=['POST'])
def submit222():
    text = request.form['textfield']
    with open('data.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.stat('data.csv').st_size == 0:
            writer.writeheader()
        writer.writerow({'text': text})
    flash('📝 Review submitted successfully!', 'success')
    return redirect(url_for('home_page'))

@app.route('/sub', methods=['GET', 'POST'])
def sub():
    if request.method == 'POST':
        # Your existing POST logic
        email = request.form['textfield']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time

        # Write to CSV
        file_exists = os.path.isfile('mail_data.csv')
        with open('mail_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['email', 'timestamp']  # Updated fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()  # Write header if file is new

            writer.writerow({
                'email': email,
                'timestamp': timestamp
            })

        flash('📝 email submitted successfully!', 'success')
        return redirect(url_for('home_page'))
    else:
        return "This is the /sub endpoint. Use POST to submit email."

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        if image.filename == '':
            flash('⚠️ No image selected!', 'warning')
            return redirect(url_for('ai_engine_page'))
        filename = image.filename
        file_path = os.path.join('static/uploads', filename)
        image.save(file_path)
        pred = prediction(file_path)
        recommendations = recommend_cosmetics(pred)
        emstore_link = emstore_info[emstore_info['disease_name'] == pred]['buy_link'].values[0] if not emstore_info[emstore_info['disease_name'] == pred].empty else '#'
        return render_template('submit.html', pred=pred, recommendations=recommendations, emstore_link=emstore_link, user=session.get('user'))


CSV_FILE = 'media/supplement_info.csv'
supplement_df = pd.read_csv(CSV_FILE)

def market():
    """Displays all skincare products grouped by skin type."""
    grouped = supplement_df.groupby(
        supplement_df['disease_name'].str.split('-').str[0].str.strip())

    data = []
    for group, df in grouped:
        data.append({
            "skin_type": group.strip(),
            "disease_name": df['disease_name'].tolist(),
            "supplement_name": df['supplement_name'].tolist(),
            "supplement_image": df['supplement_image'].tolist(),
            "buy": df['buy_link'].tolist()
        })

    return render_template('market.html', products=data)


@app.route('/market')
def market():
    user = session.get('user')
    print(supplement_info['supplement_image'])
    return render_template('market.html',
                           supplement_image=list(supplement_df['supplement_image']),
                           supplement_name=list(supplement_df['supplement_name']),
                           disease_name=list(supplement_df['disease_name']),
                           buy=list(supplement_df['buy_link']),
                           user=user)



# --- Prediction & Recommendation Functions (unchanged) ---
def prediction(image_path):
    
    def prepare(img_path):
        img = image.load_img(img_path, target_size=(224,224))
        x = image.img_to_array(img)
        x = x/255
        return np.expand_dims(x, axis=0)

    predictions = model.predict([prepare(image_path)])
    skin_types = ['Red_Spots_skin', 'Dry Skin', 'Normal Skin', 'Oily Skin', 'Scaly Skin', 'Sensitive Skin', 'Skin_moles']
    return skin_types[np.argmax(predictions)]

def recommend_cosmetics(skin_type):
    recommendations_map = {
        "Normal Skin": """For normal skin...""",
        "Sensitive Skin": """Sensitive skin requires...""",
        "Dry Skin": """Dry skin needs...""",
        "Oily Skin": """To control excess oil...""",
        "Scaly Skin": """Scaly skin often...""",
        "Red_Spots_skin": """Red spots can be...""",
        "Skin_moles": """Moles are usually..."""
    }
    return recommendations_map.get(skin_type, "Please enter a valid skin type.")

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    app.run(debug=False)