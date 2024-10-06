import re
import pdfplumber
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
import openai
import time
import tiktoken

# Load environment variables (ensure you have a .env file with API keys)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv('DATABASE_URL')

# MongoDB Client
client = MongoClient(database_url)
db = client["Learning"]
collection = db["Learning_Collection"]

# Fetch documents from MongoDB and load them into a DataFrame
documents = collection.find()
df = pd.DataFrame(list(documents))
'''
# Clean the 'description' field to remove special characters
df['description_cleaned'] = df['description'].str.lower().str.replace('[^a-zA-Z0-9\s]', '', regex=True).str.strip()

# Ensure 'amount' is a string for formatting purposes
df['amount'] = df['amount'].astype(str)

# Make sure 'transaction_type' is a string
df['transaction_type'] = df['transaction_type'].astype(str)

# Prepare the data for fine-tuning in chat format required for gpt-3.5-turbo
def format_for_openai_chat(row):
    return {
        "messages": [
            {"role": "user", "content": f"Transaction: {row['description_cleaned']}, {row['amount']}"},
            {"role": "assistant", "content": f"{row['transaction_type']}"}
        ]
    }

# Validate each JSON line to ensure it's properly formatted
def validate_json_line(json_line):
    try:
        json.loads(json_line)
        return True
    except json.JSONDecodeError as e:
        print(f"Invalid JSON line: {json_line}, error: {e}")
        return False

# Apply the formatting to the entire DataFrame
formatted_data = df.apply(format_for_openai_chat, axis=1)

# Save formatted data to a JSONL file with validation
with open('mongodb_to_finetune_chat.jsonl', 'w', encoding='utf-8') as outfile:
    for entry in formatted_data:
        json_line = json.dumps(entry)
        if validate_json_line(json_line):  # Validate the JSON line before writing
            outfile.write(json_line + '\n')

print("Data saved to mongodb_to_finetune_chat.jsonl")

# Upload the JSONL file for fine-tuning
response = openai.File.create(
    file=open("mongodb_to_finetune_chat.jsonl", "rb"),
    purpose='fine-tune'
)

file_id = response['id']
print(f"File ID: {file_id}")

# Create a fine-tuning job
fine_tune_response = openai.FineTuningJob.create(
    training_file=file_id,
    model="gpt-3.5-turbo"  # Chat-based model
)

fine_tune_id = fine_tune_response['id']
print(f"Fine-tuning Job ID: {fine_tune_id}")

# Monitor the fine-tuning process
def monitor_fine_tuning(fine_tune_id):
    while True:
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
        
        time.sleep(60)  # Check every minute

monitor_fine_tuning(fine_tune_id)
'''
# Test the fine-tuned model using the provided fine-tuned model ID
def test_fine_tuned_model(model_id, prompt):
    response = openai.ChatCompletion.create(
        model=model_id,  # Use the fine-tuned model ID
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Example prompt for testing
fine_tuned_model_id = "ft:gpt-3.5-turbo-0125:personal::AFIR5OZo"  # Replace with your fine-tuned model ID
example_prompt = "Transaction: bought groceries for 50.00"
output = test_fine_tuned_model(fine_tuned_model_id, example_prompt)  # Replace with fine-tuned model ID
print(f"Model Output: {output}")

# Token counting to ensure data is within acceptable limits
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
for entry in formatted_data:
    prompt_length = len(enc.encode(entry['messages'][0]['content']))
    completion_length = len(enc.encode(entry['messages'][1]['content']))
    print(f"Prompt Length: {prompt_length}, Completion Length: {completion_length}")
