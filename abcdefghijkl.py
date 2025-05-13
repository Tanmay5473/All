from mistralai import Mistral
import json
import pandas as pd
import os
from datetime import datetime

api_key = "SJtWzHbiHf53ptPHd2ygPHYFZslvz76u"
client = Mistral(api_key=api_key)

# Optional: Allow user to input URL or use the predefined one
# URL = input("Copy URL for PDF from your Application and paste here.")
# pdf_url = URL

# Predefined URL - uncomment the one you want to use
pdf_url = "https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/4299/NEO000004299-ICICI.pdf"

# Extract document ID from URL for naming the output files
doc_id = pdf_url.split('/')[-1].replace('.pdf', '')

# Prompt for document validation
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": """
You are an intelligent assistant for validating financial account opening documents. You will receive a PDF document for one of the following account types:

ICICI Bank Account Opening Form

---

### TASKS:

1. **Detect the account type** based on form heading in the PDF.

2. **Extract the mandatory fields** listed below based on the account type and page number.

3. **Validate**:
   - All fields must be filled (not blank, missing, or placeholder like "____").
   - Aadhaar number must be **masked** – only last 4 digits should be visible (eg., XXXX-XXXX-1234 and ).
   - On pages with checkbox-based questions, **at least one checkbox must be selected per label group**.
   
4. If there is no value then give test_status as Test Failed if value is present then give test passed.

5. There are also checkboxes for some fields need to detect them as value.

---

### MANDATORY FIELD STRUCTURE:
ICICI Bank Account Opening Form
Validate the following:

- **Page 3**: Name, Date of Birth, PAN, Occupation, Email, Mobile No, Father’s Name, Mother’s Maiden Name, Marital Status, Identity Proof Number, Type of Identity Proof, Address Proof Number, Residence Address (Particulars, City, State, Pin, Country)
- **Page 4**: Same as Page 3 (if repeated, validate again)
- **Page 5**: Communication Address (Particulars, City, State, Pin, Country), Type of Account, Income Range
- **Page 6**: Mode of Operations (for Bank/Demat), Joint Communication Preference, Standing Instructions, Nomination Option — Check that each **checkbox group has one selected**
- **Page 7**: More checkbox selections – validate one is selected per group
- **Page 8**: Name, Company, Code, Designation, Date
- **Page 11**: Name, Residential Status, Country of Birth, Citizenship, Country of Present Residence, Country of Tax Residence
- **Page 13**: Customer Declaration, Nominee Details – Check if filled
- **Page 14**: Nominee Name, Share %, Relationship, Nominee Address, Mobile, Email
- **Pages 17–22**: Full KYC for each holder: Name, Father/Mother/Spouse Name, DOB, Gender, Marital Status, Citizenship, PAN, Aadhaar (Masked), Full Address, Contact Info (Mobile, Email)
- **Pages 25–26**: Ensure at least one checkbox ticked per group
- **Page 27**: Check that Power of Attorney section is filled
- **Page 31**: Sole/First Holder Name + PAN, Second + Third Holder info

---

### OUTPUT FORMAT:
Return a JSON object strictly in the following format:
{
  "account_type": "<Detected Type>",
  "fields": [
    {
      "label": "<Field Label>",
      "value": "<Extracted Value>",
      "page_number": <Page>,
      "test_status": "Test Passed" | "Test Failed"
    }
  ],

  "aadhaar_masking_status": "Masked" | "Unmasked",
  "overall_status": "Passed" | "Failed"
}

Be strict in validation. Any missing, blank, or incorrectly masked value should mark the field as "Test Failed" also give reason why test failed.
Only respond in the structured JSON format provided above.
"""
            },
            {
                "type": "document_url",
                "document_url": pdf_url
            },
        ],
    }
]

chat_response = client.chat.complete(
    model="mistral-small-latest",
    messages=messages,
)

# Get the JSON response
json_response = chat_response.choices[0].message.content

# Print the raw response
print("Raw JSON Response:")
print(json_response)

# Parse the JSON response
try:
    # Find the JSON object in the response (in case there's any extra text)
    import re

    json_match = re.search(r'({[\s\S]*})', json_response)
    if json_match:
        json_str = json_match.group(1)
        validation_data = json.loads(json_str)
    else:
        validation_data = json.loads(json_response)

    print("\nSuccessfully parsed JSON data")

    # Save JSON to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{doc_id}_validation_{timestamp}.json"
    with open(json_filename, 'w') as json_file:
        json.dump(validation_data, json_file, indent=2)
    print(f"JSON data saved to {json_filename}")

    # Create Excel file with multiple sheets
    excel_filename = f"{doc_id}_validation_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Property': ['Account Type', 'Aadhaar Masking Status', 'Final Status'],
            'Value': [
                validation_data.get('account_type', 'N/A'),
                validation_data.get('aadhaar_masking_status', 'N/A'),
                validation_data.get('Final_status', 'N/A')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Fields sheet
        if 'fields' in validation_data:
            fields_df = pd.DataFrame(validation_data['fields'])
            fields_df.to_excel(writer, sheet_name='Fields', index=False)

        # Checkbox validation sheet
        if 'checkbox_validation' in validation_data:
            checkbox_df = pd.DataFrame(validation_data['checkbox_validation'])
            checkbox_df.to_excel(writer, sheet_name='Checkbox Validation', index=False)

    print(f"Excel data saved to {excel_filename}")

except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    print("Response may not be in valid JSON format. Check the raw output above.")
except Exception as e:
    print(f"Error processing data: {e}")