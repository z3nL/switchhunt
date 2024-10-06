import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables for OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define your fine-tuned model ID (the one you successfully trained)
fine_tuned_model_id = "ft:gpt-3.5-turbo-0125:personal::AFIR5OZo"

# Load test cases from the jsonl file
test_cases_file = "test_cases.jsonl"

def test_fine_tuned_model(model_id, messages):
    """
    Sends a test message to the fine-tuned model and returns the response.
    """
    response = openai.ChatCompletion.create(
        model=model_id,  # Use your fine-tuned model ID
        messages=messages,
        max_tokens=100,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Test the model using the cases from the test file
with open(test_cases_file, 'r') as f:
    for line in f:
        test_case = json.loads(line)
        user_message = test_case["messages"]
        output = test_fine_tuned_model(fine_tuned_model_id, user_message)
        print(f"Test Prompt: {user_message[0]['content']}")
        print(f"Model Output: {output}")
        print("---")
