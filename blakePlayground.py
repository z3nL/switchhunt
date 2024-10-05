import re
import pdfplumber

def clean_extracted_text(text):
    # Insert spaces between text and numbers, and between card numbers and amounts
    cleaned_text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)  # Add space between letters and numbers
    cleaned_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', cleaned_text)  # Add space between numbers and letters
    
    # Insert spaces between card numbers and negative amounts when they are attached
    cleaned_text = re.sub(r'(\d{4})([-\d])', r'\1 \2', cleaned_text)  # Specifically target card numbers followed by amounts
    
    # Handle multi-line descriptions by merging lines that are part of the same transaction
    cleaned_text = re.sub(r'([A-Za-z0-9 ,\.\*\-\n]+)\n([A-Za-z0-9 ,\.\*\-\n]+)', r'\1 \2', cleaned_text)
    
    return cleaned_text

def parse_pdf_transactions(file_path):
    # Initialize an empty list to hold the transaction data
    transactions = []

    # Open the PDF file using pdfplumber
    with pdfplumber.open(file_path) as pdf:
        text = ""
        # Extract text from all pages and concatenate them
        for page in pdf.pages:
            text += page.extract_text()


    # Clean the text to handle multi-line transactions and missing spaces
    cleaned_text = clean_extracted_text(text)

    # Define a regex pattern to extract transactions (date, description, and amounts)
    # We will capture the date, description, and first amount (and ignore the card number if detected)
    pattern = r'(\d{2}/\d{2})\s+([A-Za-z0-9 ,\.\*\-\n]+?)\s+(\d{4})?\s*(-?\d{1,3}(?:,\d{3})*\.\d{2})'

    # Find all matches in the cleaned text
    matches = re.findall(pattern, cleaned_text)

    # Print out the matches for debugging
    print("\n--- TRANSACTIONS DETECTED (ignoring card numbers) ---\n")
    for match in matches:
        print(match)

    # Process each match and store it in the transactions list
    for match in matches:
        date, description, _, amount = match  # We ignore the card number (the third captured group)
        # Remove commas from the amount and convert it to a float, ignoring the minus sign for uniformity
        amount = abs(float(amount.replace(",", "")))  # Use abs() to remove the minus sign
        # Clean up the description (remove any leftover newlines)
        description = description.replace('\n', ' ').strip()
        # Create a dictionary for each transaction and add it to the list (ignore the card number)
        transactions.append({
            "date": date,
            "description": description,
            "amount": amount
        })

    return transactions

# Example usage
file_path = 'CreditStatement.pdf'  # Replace with the actual path to your PDF
transactions = parse_pdf_transactions(file_path)

file_path = 'bankstatement.pdf'  # Replace with the actual path to your PDF
transactions = parse_pdf_transactions(file_path)

# Print the final parsed transactions
print("\n--- FINAL PARSED TRANSACTIONS (ignoring card numbers, minus sign removed) ---\n")
for transaction in transactions:
    print(transaction)
