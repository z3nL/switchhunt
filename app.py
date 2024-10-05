from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# from flask_mysqldb import MySQL
# import MySQLdb.cursors
import os
# import openai
from dotenv import load_dotenv
import ast
import asyncio
import datetime

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL')
@app.route('/')
def home():
    return redirect(url_for('motion'))

@app.route('/MotionBank/home')
def motion():
    return render_template('index.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run()