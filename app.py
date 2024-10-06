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

# Default -> redir to login
@app.route('/')
def default():
    if ('active' in session and session['active'] == 1):
        return redirect(url_for('home'))
    else:
        return redirect(url_for('loginpg'))

# Login page
@app.route('/MotionFinance/login')
def loginpg():
    return render_template('login.html')

# Home page
@app.route('/MotionFinance/home')
def home():
    if ('active' in session and session['active'] == 1):
        return render_template('index.html')
    else:
        return redirect(url_for('loginpg'))

@app.route('/MotionFinance/login', methods=['POST'])
async def signIn():
    username = request.form['username']
    password = request.form['password']

    # TODO Query the database!!
    if (username == "motion" and password == "motion"):
        session['active'] = 1
        return redirect(url_for('home'))
    else:
        flash('Incorrect credentials!', 'error')
        
    return redirect(url_for('loginpg'))


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
    app.run()