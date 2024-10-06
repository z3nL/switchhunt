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
    print("---\nNo env file!\n---\n")
database_url = os.getenv('DATABASE_URL')
client = MongoClient(database_url)
db = client['UserInfo']

# Home page redirect
@app.route('/')
def login():
    return render_template('login.html')


# Home page
@app.route('/MotionFinance/home')
def home():
    return render_template('index.html')

# Connection testing
@app.route('/test-connection')
def test_connection():
    try:
        # Check MongoDB server information
        server_info = client.server_info()  # Will throw an exception if not connected
        print("MongoDB: We're good!")
        return redirect(url_for('home'))
    except Exception as e:
        print (f"Failed to connect to MongoDB Atlas: {e}")
        return redirect(url_for('home'))

# Run app
if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)