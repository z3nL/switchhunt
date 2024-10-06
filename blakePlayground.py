import re
import pdfplumber
import pandas as pd


# Function to clean the extracted text
def clean_extracted_text(text):
    # Insert spaces between text and numbers, and between card numbers and amounts
    cleaned_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)  # Add space between letters and numbers
    cleaned_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_text)  # Add space between numbers and letters

    # Insert spaces between card numbers and negative amounts when they are attached
    cleaned_text = re.sub(r'(\d{4})([-\d])', r'\1 \2',
                          cleaned_text)  # Specifically target card numbers followed by amounts

    # Handle multi-line descriptions by merging lines that are part of the same transaction
    cleaned_text = re.sub(r'([A-Za-z0-9 ,\.\*\-\n]+)\n([A-Za-z0-9 ,\.\*\-\n]+)', r'\1 \2', cleaned_text)

    return cleaned_text


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
        transactions.append({
            "date": date,
            "description": description,
            "amount": amount
        })


# Filter out invalid dates or unwanted descriptions like interest charges
def is_valid_date(date):
    return bool(re.match(r'\d{2}/\d{2}', date))


# Filter out transactions with unwanted descriptions (e.g., "Interest", "Fee", etc.)
def is_valid_transaction(description):
    # List of keywords to exclude
    unwanted_keywords = ["Interest", "Fee", "Charge", "Balance Transfer", "Cash Advance", "- 0 -"]
    return not any(keyword in description for keyword in unwanted_keywords)


# Example usage
transactions = []

file_path = '20240914-statements-8356-.pdf'  # Replace with your PDF path
parse_pdf_transactions(file_path, transactions)

# Filter out invalid transactions
filtered_transactions = [
    t for t in transactions if is_valid_date(t['date']) and is_valid_transaction(t['description'])
]

# Create a DataFrame
df = pd.DataFrame(filtered_transactions)

# Print the DataFrame
print(df)
