import re
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from datasets import Dataset
import json
import openai
import time

# Input DB upload choice
choiceDB = input("Upload to DB? Y = Yes: ")

<<<<<<< HEAD
# Function to clean extracted text
=======

# Function to clean the extracted text
>>>>>>> c1caf43ef9d0003bc6292edc4e5cc52a286eee2b
def clean_extracted_text(text):
    cleaned_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    cleaned_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_text)
    cleaned_text = re.sub(r'(\d{4})([-\d])', r'\1 \2', cleaned_text)
    cleaned_text = re.sub(r'([A-Za-z0-9 ,\.\*\-\n]+)\n([A-Za-z0-9 ,\.\*\-\n]+)', r'\1 \2', cleaned_text)
    return cleaned_text

# Categorize transactions
def categorize_transaction(description):
    description = description.lower()
    if any(keyword in description for keyword in ["payment", "deposit", "refund", "income"]):
        return "Income"
    elif any(keyword in description for keyword in ["grocery", "food", "restaurant", "gas", "fuel", "shopping"]):
        return "Expense"
    elif any(keyword in description for keyword in ["transfer", "cash", "balance"]):
        return "Transfer"
    else:
        return "Other"

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
        transaction_type = categorize_transaction(description)
        transactions.append({
            "date": date,
            "description": description,
            "amount": amount,
            "transaction_type": transaction_type
        })

# Filtering functions
def is_valid_date(date):
    return bool(re.match(r'\d{2}/\d{2}', date))

def is_valid_transaction(description, amount):
    unwanted_keywords = ["Interest", "Fee", "Charge", "Balance Transfer", "Cash Advance", "- 0 -", "Payment"]
    unwanted_amounts = [1114.43, 545.41]
    return not any(keyword in description for keyword in unwanted_keywords) and amount not in unwanted_amounts

# Example usage - parsing PDF
transactions = []
file_paths = ['bankstatement.pdf']
for file_path in file_paths:
    parse_pdf_transactions(file_path, transactions)

# Filter invalid transactions
filtered_transactions = [
    t for t in transactions if is_valid_date(t['date']) and is_valid_transaction(t['description'], t['amount'])
]

# Convert to DataFrame
df = pd.DataFrame(filtered_transactions)

# Connect to MongoDB
if not load_dotenv():
    print("---\nNo env file!\n---\n")
database_url = os.getenv('DATABASE_URL')
openai.api_key = os.getenv("OpenAI_API_KEY")

client = MongoClient(database_url)
db = client["Learning"]
collection = db["Learning_Collection"]

if filtered_transactions and choiceDB == 'Y':
    collection.insert_many(filtered_transactions)
    print(f"Inserted {len(filtered_transactions)} transactions into MongoDB.")
else:
    print("No transactions to insert.")

# Convert DataFrame to JSONL for fine-tuning
df['description_cleaned'] = df['description'].str.lower().str.replace('[^a-zA-Z0-9\s]', '', regex=True).str.strip()
df['date'] = pd.to_datetime(df['date'], format='%m/%d')
df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

<<<<<<< HEAD
# Ensure 'transaction_type' stays as string, no encoding to numbers
if 'transaction_type' not in df.columns:
    raise KeyError("'transaction_type' column is missing.")

# No more LabelEncoder here. Use transaction_type as string.
X_train, X_test, y_train, y_test = train_test_split(df['description_cleaned'], df['transaction_type'], test_size=0.3, random_state=42)

train_data = pd.DataFrame({'description_cleaned': X_train, 'transaction_type': y_train})
train_dataset = Dataset.from_pandas(train_data)

# Ensure completion is stored as a string
def format_for_openai(row):
    return {"prompt": f"Transaction: {row['description_cleaned']}, {row['amount']}", 
            "completion": row['transaction_type']}

formatted_data = df.apply(format_for_openai, axis=1)

with open('transaction_data.jsonl', 'w') as outfile:
    for entry in formatted_data:
        json.dump(entry, outfile)
        outfile.write('\n')

# Fine-tuning with OpenAI
response = openai.File.create(file=open("transaction_data.jsonl", "rb"), purpose='fine-tune')
file_id = response['id']

fine_tune_response = openai.FineTuningJob.create(training_file=file_id, model="gpt-3.5-turbo")
fine_tune_id = fine_tune_response['id']

# Monitor Fine-Tuning
def monitor_fine_tuning_v2(fine_tune_id):
    while True:
        try:
            fine_tune_status = openai.FineTuningJob.retrieve(id=fine_tune_id)
            status = fine_tune_status['status']
            print(f"Fine-tuning status: {status}")
            if status == 'succeeded':
                print("Fine-tuning succeeded!")
                model_id = fine_tune_status['fine_tuned_model']
                print(f"Fine-tuned Model ID: {model_id}")
                break
            elif status == 'failed':
                print("Fine-tuning failed.")
                break
            time.sleep(60)
        except openai.error.InvalidRequestError as e:
            print(f"Error retrieving fine-tuning job: {e}")
            break

monitor_fine_tuning_v2(fine_tune_id)
=======
'''---------------------------------------------------PIE CHART---------------------------------------------------'''


def create_pie(dataframe, exclude_categories=None, output_file="pie_chart.png"):
    # Group by transaction type and sum the amounts
    pie_data = dataframe.groupby('transaction_type')['amount'].sum()

    # Exclude specified categories if provided
    if exclude_categories:
        pie_data = pie_data[~pie_data.index.isin(exclude_categories)]

    # Check if there's any data left to plot
    if pie_data.empty:
        print("No data available to display.")
        return

    # Create a pie chart
    plt.figure(figsize=(8, 6))
    # Set font properties
    font_properties = {'weight': 'bold', 'size': 12}  # Bold font

    # Create the pie chart without percentages
    plt.pie(pie_data, labels=pie_data.index, labeldistance=1.1, startangle=140, textprops=font_properties)
    plt.title('Transaction Amounts by Type', fontsize=14, fontweight='bold')  # Bold title
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular

    # Save the pie chart as a PNG file
    plt.savefig(output_file, format='png', bbox_inches='tight')

    # Show the pie chart
    plt.show()


create_pie(df, exclude_categories=[], output_file="my_pie_chart.png")
>>>>>>> c1caf43ef9d0003bc6292edc4e5cc52a286eee2b
