import re
import pdfplumber
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

'''-------------------------------------------INPUT OUTPUT---------------------------------------------------'''
choiceDB = input("Upload to DB? Y = Yes: ")




# Function to clean the extracted text
def clean_extracted_text(text):
    cleaned_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)  # Add space between letters and numbers
    cleaned_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_text)  # Add space between numbers and letters
    cleaned_text = re.sub(r'(\d{4})([-\d])', r'\1 \2', cleaned_text)  # Insert spaces between card numbers and amounts
    cleaned_text = re.sub(r'([A-Za-z0-9 ,\.\*\-\n]+)\n([A-Za-z0-9 ,\.\*\-\n]+)', r'\1 \2',
                          cleaned_text)  # Handle multi-line descriptions
    return cleaned_text


# Function to categorize the transaction based on description
def categorize_transaction(description):
    description = description.lower()

    # Categories based on keywords in the description
    if any(keyword in description for keyword in ["payment", "deposit", "refund", "income"]):
        return "Income"
    elif any(keyword in description for keyword in ["grocery", "food", "restaurant", "gas", "fuel", "shopping"]):
        return "Expense"
    elif any(keyword in description for keyword in ["transfer", "cash", "balance"]):
        return "Transfer"
    else:
        return "Other"


# Function to parse PDF transactions
def parse_pdf_transactions(file_path, transactions):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    # Clean the text
    cleaned_text = clean_extracted_text(text)

    # Define a regex pattern to extract transactions (date, description, and amounts)
    pattern = r'(\d{2}/\d{2})\s+([A-Za-z0-9 ,\.\*\-\n]+?)\s+(\d{4})?\s*(-?\d{1,3}(?:,\d{3})*\.\d{2})'
    matches = re.findall(pattern, cleaned_text)

    # Process each match and store it in the transactions list
    for match in matches:
        date, description, _, amount = match
        amount = abs(float(amount.replace(",", "")))  # Convert to float and use abs() to remove minus
        description = description.replace('\n', ' ').strip()
        transaction_type = categorize_transaction(description)  # Add transaction type
        transactions.append({
            "date": date,
            "description": description,
            "amount": amount,
            "transaction_type": transaction_type  # Add the transaction type to the data
        })


# Function to filter out invalid dates
def is_valid_date(date):
    return bool(re.match(r'\d{2}/\d{2}', date))


# Function to filter out transactions with unwanted descriptions or amounts
def is_valid_transaction(description, amount):
    # List of keywords to exclude
    unwanted_keywords = ["Interest", "Fee", "Charge", "Balance Transfer", "Cash Advance", "- 0 -", "Payment"]

    # Remove duplicates like the 1114.43 or 545.41 payment examples
    unwanted_amounts = [1114.43, 545.41]

    # Exclude transactions containing unwanted keywords or amounts
    return not any(keyword in description for keyword in unwanted_keywords) and amount not in unwanted_amounts


# Example usage
transactions = []

# Parse transactions from PDF
file_paths = ['CreditStatement.pdf', 'bankstatement.pdf','bankstatement2.pdf','bankstatement3.pdf','bankstatement4.pdf','bankstatement5.pdf','bankstatement6.pdf']  # List of your PDF files
for file_path in file_paths:
    parse_pdf_transactions(file_path, transactions)

# Filter out invalid transactions
filtered_transactions = [
    t for t in transactions if is_valid_date(t['date']) and is_valid_transaction(t['description'], t['amount'])
]

# Create a DataFrame from the filtered transactions
df = pd.DataFrame(filtered_transactions)

# Print the DataFrame to see the output including the transaction type
print(df)

'''-------------------------------------------CONNECT TO DATABASE---------------------------------------------------'''
if not load_dotenv():
    print("---\nNo env file!\n---\n")
database_url = os.getenv('DATABASE_URL')

# Connect to MongoDB
client = MongoClient(database_url)
db = client["Learning"]  # Replace with your database name
collection = db["Learning_Collection"]  # Replace with your collection name

# Insert the filtered transactions into MongoDB
if filtered_transactions and choiceDB == 'Y':
    collection.insert_many(filtered_transactions)
    print(f"Inserted {len(filtered_transactions)} transactions into MongoDB.")
else:
    print("No transactions to insert.")

'''-------------------------------------------GRAB FROM DATABASE---------------------------------------------------'''
documents = collection.find()  # Fetch all documents
data_list = []  # List to store the data
for document in documents:
    data_list.append(document)  # Append each document to the list
df = pd.DataFrame(data_list)






#machine learning start idk how to work this



from pymongo import MongoClient

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import pandas as pd

client = MongoClient('mongodb+srv://zen33:zen@squad.vab1r.mongodb.net/?retryWrites=true&w=majority&appName=Squad')
db = client['learning']
collection = ['learning_collection']

df['date'] = pd.to_datetime(df['date'], format='%m/%d')  # Assuming no year info, use month/day
df['day'] = df['date'].dt.day
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek  # 0 = Monday, 6 = Sunday


from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(max_features=500)  # Limit the number of features to avoid overfitting
description_vectors = vectorizer.fit_transform(df['description'])

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
df['amount_normalized'] = scaler.fit_transform(df[['amount']])


from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
df['transaction_type_encoded'] = label_encoder.fit_transform(df['transaction_type'])


import pandas as pd

# One-hot encode the 'transaction_type' column
df_one_hot_encoded = pd.get_dummies(df, columns=['transaction_type'])

# This will create separate binary columns for each unique value in 'transaction_type'
print(df_one_hot_encoded.head())



