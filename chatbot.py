import openai
import json
import os
from dotenv import load_dotenv

if not load_dotenv():
    print("---\nNo env file!\n---\n")
os.getenv('OPENAI_API_KEY')
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to load transactions from the JSONL file
def load_transactions_from_jsonl(file_path):
    transactions = []
    
    # Check if file exists and is accessible
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return transactions
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    transactions.append(json.loads(line))  # Each line is a JSON object
                except json.JSONDecodeError as e:
                    print(f"Error parsing line in {file_path}: {e}")
        print(f"Loaded {len(transactions)} transactions.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return transactions

# Function to generate chatbot response
def chatbot_response(user_input, transactions_info):
    # Extended keyword list to include more queries related to files, data, and transactions
    keywords = ["transactions", "show me my transactions", "recent transactions", "file", "data", "history", "records", "expenses", "purchases", "transaction history", "bank history", "spending"]
    
    # Check if the user is asking about transactions or related topics
    if any(keyword in user_input.lower() for keyword in keywords):
        combined_input = f"{user_input}\nHere are some recent transactions: {transactions_info}"
    else:
        combined_input = user_input  # Don't include transaction info unless explicitly asked
    
    try:
        # Call the OpenAI API with a prompt
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": combined_input}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7
        )
        # Extracting the chatbot response
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Sorry, something went wrong when trying to process your request."

if __name__ == "__main__":
    # Load the transactions from the JSONL file
    file_path = "parsed_pdf_transactions.jsonl"
    transactions = load_transactions_from_jsonl(file_path)  # Read transactions from JSONL file
    
    if not transactions:
        print("No transactions loaded. Exiting...")
        exit()
    
    # Convert the transaction info into a summary or a string
    transactions_info = "\n".join([f"Transaction: {t['messages'][0]['content']}, Type: {t['messages'][1]['content']}" for t in transactions[:]])  # For brevity, use first 5 transactions

    # Proceed with chatbot interactions
    print("Chatbot is ready! Type 'exit' to end.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        # Only pass transaction info if the user explicitly asks for it
        bot_response = chatbot_response(user_input, transactions_info)
        print(f"Bot: {bot_response}")
