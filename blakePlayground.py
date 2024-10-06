import re
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
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
file_paths = ['20240914-statements-8356-.pdf']  # List of your PDF files
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


'''---------------------------------------------------PIE CHART---------------------------------------------------'''
# Group by transaction type and sum the amounts
pie_data = df.groupby('transaction_type')['amount'].sum()

# Create a pie chart
plt.figure(figsize=(8, 6))
plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140)
plt.title('Transaction Amounts by Type')
plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
plt.show()



