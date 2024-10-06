import openai
import json
import os
from dotenv import load_dotenv

# Load environment variables
if not load_dotenv():
    print("---\nNo env file!\n---\n")
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

# Function to filter transactions based on user input
def filter_transactions(user_input, transactions):
    relevant_transactions = []
    
    # Filter transactions based on the keywords in the user input
    for transaction in transactions:
        if any(keyword.lower() in transaction['messages'][0]['content'].lower() for keyword in user_input.split()):
            relevant_transactions.append(transaction)
    
    return relevant_transactions

# Function to generate chatbot response with all filtered transactions
def chatbot_response(conversation_history, user_input, transactions):
    # Filter transactions based on the user input
    relevant_transactions = filter_transactions(user_input, transactions)
    
    # Convert the relevant transactions into a summary string
    if relevant_transactions:
        transactions_info = "\n".join([f"Transaction: {t['messages'][0]['content']}, Type: {t['messages'][1]['content']}" for t in relevant_transactions])
    else:
        transactions_info = "No relevant transactions found."

    # Add the current user input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Prepare a system message with all the relevant transactions
    system_message = {"role": "system", "content": f"Here are all the relevant transactions: {transactions_info}"}

    try:
        # Generate the final chatbot response with a large enough token limit
        final_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history + [system_message],
            max_tokens=2048,  # Set max tokens high to return as many transactions as possible
            temperature=0.7
        )
        
        # Add the bot's response to the conversation history
        bot_message = final_response['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": bot_message})
        
        return bot_message
    
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
    
    # Maintain conversation history
    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]

    # Proceed with chatbot interactions
    print("Chatbot is ready! Type 'exit' to end.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        # Pass the conversation history, user input, and transactions to the chatbot response function
        bot_response = chatbot_response(conversation_history, user_input, transactions)
        print(f"Bot: {bot_response}")
