from flask import Flask, render_template, send_file, request, redirect, url_for, flash, session, jsonify
# from flask_mysqldb import MySQL
# import MySQLdb.cursors
import os
# import openai
from dotenv import load_dotenv
import configparser
from pymongo import MongoClient
import ast
import asyncio
import datetime

# Set up app and MongoDB connection
app = Flask(__name__)
if not load_dotenv():
    print("---\nDid you make a .env file and add DATABASE_URL to it? -Zen\n---\n")
database_url = os.getenv('DATABASE_URL')
client = MongoClient(database_url)
db = client['Squad']

# Home page redirect
@app.route('/')
def home():
    return redirect(url_for('motion'))

# Home page
@app.route('/MotionBank/home')
def motion():
    return render_template('index.html')

# Connection testing
@app.route('/test-connection')
def test_connection():
    try:
        # Check MongoDB server information
        server_info = client.server_info()  # Will throw an exception if not connected
        return send_file('static/images/preston.jpeg', mimetype='image/jpeg')
    except Exception as e:
        return f"Failed to connect to MongoDB Atlas: {e}"

# Run app
if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)