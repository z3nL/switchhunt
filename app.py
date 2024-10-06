from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pandas as pd
from helpers import create_pie
from helpers import extractCo
import chatbot
from helpers import bBotTip
from helpers import parse_pdf_and_create_jsonl
import openai

# Set up app, OpenAI, and MongoDB connection
app = Flask(__name__)

if not load_dotenv():
    print("---\nNo env file!\n---\n")

openai.api_key = os.getenv('OPENAI_API_KEY')

database_url = os.getenv('DATABASE_URL')
client = MongoClient(database_url)
db = client['UserInfo']
logins = db['logins']
allTsacs = []
tsac_data = []
transaction_data = {}; transaction_totals = {}

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
async def home():
    if ('active' in session and session['active'] == 1):
        username = session['username']
        
        db = client['Learning']
        entries = db['New2']
        ts_data = {}; ts_totals = {}
        trTypes = ["Automotive/Gas", "Entertainment", "Rent/Utility", "Food", "Supplies", "Medical"]
        for type in trTypes:
            transactions = list(entries.find({"transaction_type":type}))
            # Convert ObjectId to string and store transactions
            ts_data[f'{type}_transactions'] = [
                {**transaction, "_id": str(transaction["_id"])} for transaction in transactions
            ]
            total = 0
            for transaction in ts_data[f'{type}_transactions']:
                total += transaction['amount']
            ts_totals[f'{type}'] = round(total, 2)
        global transaction_data; global transaction_totals
        transaction_data = ts_data; transaction_totals = ts_totals
        #session['transaction_data'] = transaction_data
        #session['transaction_totals'] = transaction_totals
        tsacs = list(entries.find().sort("date", -1))
        global allTsacs
        allTsacs =  [
            {**tsac, "_id": str(tsac["_id"])} for tsac in tsacs
        ]
        df = pd.DataFrame(allTsacs)
        await create_pie(df, 'transaction_type', exclude_categories=[], output_file="./static/images/financepie.png")
        
        #ts_data = session['transaction_data']
        #ts_totals = session['transaction_totals'] global allTsacs transaction_data transaction_totals
        return render_template('index.html', username=username, transaction_data=transaction_data, \
                                            transaction_totals=transaction_totals, allTsacs=allTsacs)
    else:
        return redirect(url_for('loginpg'))

# Specific category page
@app.route('/specific')
async def specific():
    if ('active' in session and session['active'] == 1):
        username = session['username']  
        category = request.args.get('category')
        global transaction_data
        tsac_data = transaction_data[f"{category}_transactions"]
        if not tsac_data:
            return redirect(url_for('home'))
        for tsac in tsac_data:
            tsac['description'] = await extractCo(tsac['description'], openai)
        tip = await bBotTip(tsac, openai)
        global transaction_totals
        tsac_total = transaction_totals[category]
        df = pd.DataFrame(tsac_data)
        await create_pie(df, 'description', exclude_categories=[], output_file="./static/images/specpie.png")
        return render_template('specific.html', tsac_data=tsac_data, category=category, username=username,\
                                                tip=tip, tsac_total=tsac_total)
    else:
        return redirect(url_for('loginpg'))

# Profile/Upload page
@app.route('/MotionFinance/profile')
async def profile():
    if ('active' in session and session['active'] == 1):
        username=session['username']
        return render_template('profile.html', username=username)
    else:
        return redirect(url_for('loginpg'))

# Upload files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file:
        filepath = os.path.join('./static/uploads', "newstatement")
        file.save(filepath)
        parsed_transactions = parse_pdf_and_create_jsonl(filepath)
        db = client['Learning']
        collection = db["New2"]
        collection.insert_many(parsed_transactions)
        print(f"Inserted {len(parsed_transactions)} transactions into MongoDB.")
        flash(f'File {file.filename} successfully uploaded!', 'success')
        messages = get_flashed_messages()
        return redirect(url_for('home'))

@app.route('/MotionFinance/login', methods=['POST'])
async def signIn():
    if ('active' in session and session['active'] == 1):
        return redirect(url_for('home'))
  
    username = request.form['username']
    password = request.form['password']

    query = {"username":username}
    user = logins.find_one(query)

    if (user and user['password'] == password):
        session['active'] = 1
        session['username'] = username
        session['password'] = password
        
        return redirect(url_for('home'))
    else:
        flash('Incorrect credentials!', 'error')
        
    return redirect(url_for('loginpg'))

# Sign out and remove png
@app.route('/logout')
def logout():
    session.clear()
    try:
        os.remove("./static/images/financepie.png")
        os.remove("./static/images/specpie.png")
        os.remove("./static/uploads/newstatement.pdf")
    except FileNotFoundError:
        pass  
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