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

# Function to generate chatbot response with filtered transactions
def chatbot_response(conversation_history, user_input, transactions, start_index=0, items_per_page=5):
    # Filter transactions based on the user input
    relevant_transactions = filter_transactions(user_input, transactions)
    
    # Paginate transactions, showing a subset of transactions at a time
    if relevant_transactions:
        paginated_transactions = relevant_transactions[start_index:start_index + items_per_page]
        transactions_info = "\n".join([f"Transaction: {t['messages'][0]['content']}, Type: {t['messages'][1]['content']}" for t in paginated_transactions])
    else:
        transactions_info = "No relevant transactions found."
    
    # Add user input to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Prepare system message with relevant transactions
    system_message = {"role": "system", "content": f"Here are some relevant transactions: {transactions_info}"}

    try:
        # Generate the final chatbot response
        final_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history + [system_message],
            max_tokens=500,  # Increase max tokens to handle larger responses
            temperature=0.7
        )
        
        # Add bot's response to the conversation history
        bot_message = final_response['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": bot_message})
        
        # Check if more transactions are available and prompt the user
        if len(relevant_transactions) > start_index + items_per_page:
            bot_message += "\n\nWould you like to see more transactions? (yes/no)"

        return bot_message, start_index + items_per_page if len(relevant_transactions) > start_index + items_per_page else None
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Sorry, something went wrong when trying to process your request.", None

if __name__ == "__main__":
    # Load the transactions from the JSONL file
    file_path = "parsed_pdf_transactions.jsonl"
    transactions = load_transactions_from_jsonl(file_path)  # Read transactions from JSONL file
    
    if not transactions:
        print("No transactions loaded. Exiting...")
        exit()
    
    # Maintain conversation history
    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]
    start_index = 0
    items_per_page = 5

    # Proceed with chatbot interactions
    print("Chatbot is ready! Type 'exit' to end.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        # Pass conversation history, user input, and transactions to the chatbot response function
        bot_response, next_start_index = chatbot_response(conversation_history, user_input, transactions, start_index, items_per_page)
        print(f"Bot: {bot_response}")
        
        # Handle pagination if more transactions are available
        if next_start_index:
            more_input = input("You: ")
            if more_input.lower() == 'yes':
                start_index = next_start_index  # Continue showing the next set of transactions
            else:
                start_index = 0  # Reset pagination
