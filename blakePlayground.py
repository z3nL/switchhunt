
# Load model directly
from transformers import AutoImageProcessor, AutoModelForObjectDetection
import pytesseract
from pdf2image import convert_from_path






processor = AutoImageProcessor.from_pretrained("farhanishraq/table_tr-finetuned-bs")
model = AutoModelForObjectDetection.from_pretrained("farhanishraq/table_tr-finetuned-bs")

# Convert PDF to images
pages = convert_from_path('bankstatement.pdf')

# Iterate through pages and extract text using pytesseract
text = ""
for page in pages:
    text += pytesseract.image_to_string(page)

print(text)  #







