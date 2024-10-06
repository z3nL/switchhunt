import openai
import re
import pdfplumber
import json
import openai
import plotly.express as px

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


async def create_pie(dataframe, identifier, exclude_categories=None, output_file="pie_chart.png"):
    if identifier not in dataframe.columns:
        print(f"Error: The identifier '{identifier}' is not a column in the dataframe.")
        return
    else:
        print(f"valid identifier!")
    
    # Group by transaction type and sum the amounts
    pie_data = dataframe.groupby(identifier)['amount'].sum().reset_index()

    # Exclude specified categories if provided
    if exclude_categories:
        pie_data = pie_data[~pie_data.index.isin(exclude_categories)]

    # Check if there's any data left to plot
    if pie_data.empty:
        print("No data available to display.")
        return

    # Create the pie chart using Plotly
    fig = px.pie(
        pie_data,
        names=identifier,  # Category labels
        values='amount',  # Values for pie chart
        title='',  # Chart title
    )
     
    # Save the pie chart as a png with kaleido
    fig.write_image(output_file)
    
# Use ChatGPT to extract the company name out of a transaction description
async def extractCo(description, openai):
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are tasked with extracting the name of a company or organization"
                    " from a bank transaction description. Ignore irrelevant words or codes"
                    " such as 'TST*', 'POS', location names, or other non-company identifiers."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given the bank transaction description: '{description}', "
                    "please return only the company/organization name involved."
                    "do NOT return a complete sentence. ONLY return a name."
                )
            }
        ]
    )
    response = completion['choices'][0]['message']['content'].strip()
    return response

# Use ChatGPT to analyze transaction sets and return financial management tips
async def bBotTip(transaction_set, openai):
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert financial advisor. You analyze transaction histories to identify patterns,"
                    " habits, and behaviors that can help optimize personal finances, reduce unnecessary expenses,"
                    " and improve saving strategies."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given the following set of bank transactions: '{transaction_set}',"
                    " identify any potential spending patterns, overspending habits, or areas"
                    " where I can save more. Provide **one actionable financial tip**"
                    " that could help me manage my money more effectively"
                    " in **TWO SENTENCES OR LESS**."
                )
            }
        ]
    )
    response = completion['choices'][0]['message']['content'].strip()
    return response