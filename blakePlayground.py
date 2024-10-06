import re
import pdfplumber
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv('DATABASE_URL')

# MongoDB Client setup
client = MongoClient(database_url)
db = client["Learning"]
collection = db["NEw"]

# Input DB upload choice
choiceDB = input("Upload to DB? Y = Yes: ")

# Function to clean extracted text from PDF
def clean_extracted_text(text):
    cleaned_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    cleaned_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_text)
    cleaned_text = re.sub(r'(\d{4})([-\d])', r'\1 \2', cleaned_text)
    cleaned_text = re.sub(r'([A-Za-z0-9 ,\.\*\-\n]+)\n([A-Za-z0-9 ,\.\*\-\n]+)', r'\1 \2', cleaned_text)
    return cleaned_text

# Filtering function to ignore unwanted transactions
def is_valid_transaction(description, amount):
    unwanted_keywords = ["Interest", "Fee", "Charge", "Balance Transfer", "Cash Advance", "Payment to Chase Card"]
    unwanted_amounts = [1114.43, 545.41]  # Add any other amounts to ignore
    return not any(keyword in description for keyword in unwanted_keywords) and amount not in unwanted_amounts

# Parse PDF transactions
def parse_pdf_transactions(file_path, transactions):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    cleaned_text = clean_extracted_text(text)
    pattern = r'(\d{2}/\d{2})\s+([A-Za-z0-9 ,\.\*\-\n]+?)\s+(\d{4})?\s*(-?\d{1,3}(?:,\d{3})*\.\d{2})'
    matches = re.findall(pattern, cleaned_text)
    for match in matches:
        date, description, _, amount = match
        amount = abs(float(amount.replace(",", "")))
        description = description.replace('\n', ' ').strip()

        # Filter out invalid transactions
        if is_valid_transaction(description, amount):
            transactions.append({
                "date": date,
                "description": description,
                "amount": amount
            })

# Function to send each transaction description to the fine-tuned model
def get_transaction_type(description, amount):
    prompt = f"Transaction: {description}, {amount}"
    response = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0125:personal::AFIR5OZo",  # Your fine-tuned model ID
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Function to create a JSONL file from parsed PDF and use the model to categorize transaction type
def parse_pdf_and_create_jsonl(file_path):
    transactions = []
    parse_pdf_transactions(file_path, transactions)
    
    # Create a list of formatted data for JSONL
    formatted_data = []
    
    for transaction in transactions:
        # Use the fine-tuned model to predict transaction type
        transaction_type = get_transaction_type(transaction['description'], transaction['amount'])
        transaction["transaction_type"] = transaction_type
        
        # Format for OpenAI chat-style JSONL
        formatted_data.append({
            "messages": [
                {"role": "user", "content": f"Transaction: {transaction['description']}, {transaction['amount']}"},
                {"role": "assistant", "content": transaction_type}
            ]
        })
    
    # Save the results to a JSONL file
    jsonl_file_path = 'parsed_pdf_transactions.jsonl'
    with open(jsonl_file_path, 'w', encoding='utf-8') as outfile:
        for entry in formatted_data:
            json.dump(entry, outfile)
            outfile.write('\n')
    
    print(f"Data saved to {jsonl_file_path}")
    
    return transactions  # Return the transactions for further use (MongoDB insert, etc.)

# Example usage: parsing a PDF and saving the results to MongoDB
file_path = 'bankstatement.pdf'  # Your PDF file
parsed_transactions = parse_pdf_and_create_jsonl(file_path)

# If user chooses to upload to MongoDB
if parsed_transactions and choiceDB == 'Y':
    collection.insert_many(parsed_transactions)
    print(f"Inserted {len(parsed_transactions)} transactions into MongoDB.")
else:
    print("No transactions to insert.")
