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

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL')
client = MongoClient(database_url)
db = client['Squad']

@app.route('/')
def home():
    return redirect(url_for('motion'))

@app.route('/MotionBank/home')
def motion():
    return render_template('index.html')

#config = configparser.ConfigParser()
#config.read(os.path.abspath(os.path.join(".ini")))

@app.route('/test-connection')
def test_connection():
    try:
        # Check MongoDB server information
        server_info = client.server_info()  # Will throw an exception if not connected
        return send_file('static/images/preston.jpeg', mimetype='image/jpeg')
    except Exception as e:
        return f"Failed to connect to MongoDB Atlas: {e}"

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)