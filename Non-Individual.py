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
pdf_url = "https://startuat.theneoworld.com/ClientDocuments//Businesswise/Non-Individual/Typefive/Pdf/5803/NEO000005803-TradingDemat.pdf"
    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/Non-Individual/Typeone/Pdf/6032/NEO000006032-TradingDemat.pdf"

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

1. Trading and Demat Account Opening Form – Non-individual
2. HUF Non-Individual Account Opening Form
3. Private Limited Non-Individual Account Opening Form
4. LLP Non-Individual Account Opening Form

---

### TASKS:

1. **Detect the account type** based on form heading in the PDF.
2. **Extract data from pdf and then extract the mandatory fields listed.
3. **Extract the mandatory fields** listed below based on the account type and page number.

4. **Validate**:
   - All fields must be filled (not blank, missing, or placeholder like "____").
   - Aadhaar number must be **masked** – only last 4 digits should be visible (e.g., XXXX-XXXX-1234).
   - On pages with checkbox-based questions, **at least one checkbox must be selected per label group**.
   - ✅ **Nominee** and **Second/Third Holder** fields are **optional**:
    - If values are present, validate them.
    - If all values are blank or the section is clearly marked "Opted Out", **do not fail the test**—assume the user has opted out.
 Based on the detected account type, extract ONLY the fields relevant to that type (page-wise).

 5. If there is no value then give status as test passed or failed.

✅ DO NOT use fields from other account types.
✅ DO NOT hallucinate field labels that are not explicitly shown in the document.
✅ DO NOT repeat the same field over and over again.

---

### MANDATORY FIELD STRUCTURE:

#### 1. Trading and Demat Account Opening Form – Non-individual

- **Page 1**: Client Name, Account Opening Date, Form
- **Page 5**: Application Number, Application Type, PAN, Name, Date of Incorporation, Place of Incorporation, Date of Commencement, Registration No., Entity Type, Registered Address: Line 1, City, District, Pin Code, State, Country
- **Page 6**: Correspondence Address: Line 1, City, District, Pin Code, State, Country, Mobile, Email ID, Related Persons, Date, Place
- **Pages 8–9, 11–15, 17–18**: Related Person KYC: Name, PAN, DOB, Gender, Aadhaar, DIN, Addresses, Email, Mobile
- **Page 20**: First Holder Name, PAN, Nationality, Gross Income, Net Worth, Occupation
- **Page 22**: Bank Proof Submitted, Account Type, Bank Name, Account Number, Branch Address, IFSC, MICR
- **Pages 21, 23, 24, 30, 31, 35, 65**: Ensure at least one checkbox ticked per label group
- **Page 36**: Entity name, Tax Address, Entity Type, Country of Incorporation, Mobile, Identification info
- **Page 38**: Controlling Person: Name, Country of Tax Residency, Identification No., Identification Type, Person Type
- **Page 62**: First Applicant full profile (Contact, Income, PEP, FATCA, etc.)
- **Page 63**: Bank Mandate: Bank Name, Branch, Account No., IFSC
- **Page 64**: FATCA Info: PAN, Incorporation, Gross Income, Net Worth, Country of Tax Residence

---

#### 2. HUF Non-Individual Form

**Page 1**: Client Name, Account Opening Date, Form
**Page 5**: Application Number, Application Type, PAN, Name, Date of Incorporation, Place of Incorporation, Date of Commencement, Registration Number, Entity Type, PROOF OF IDENTITY, Registered Address: Line 1, City, District, Pin Code, State, Country
**Page 6**: Correspondence Address, Mobile, Email ID, Related Persons, Date, Place
**Page 8**: Application Number, Application Type, Name, Maiden Name, Father /Spouse's Name, Mother Name, Date of Birth, Gender, Nationality, Related Person Type, Registered Address
**Page 9**: Permanent residence address, Line 1, City/Town/Village, District, Pin Code, State, Country, Address Type, Aadhaar, Mobile, Email ID, Date, Place
**Page 11**: Gross annual income range p.a., Occupation
**Page 12**: Additional Details
**Page 13**: Bank Details: Account Type, Bank Name, Bank Account No., Branch Address, IFSC, MICR
**Page 14**: SMS Alert & Trust Facility, Option for Delivery Instruction Booklet (checkbox)
**Page 15**: Check one checkbox ticked for every label group
**Page 21**: Check one checkbox ticked for every label group
**Page 22**: Check one checkbox ticked for every label group
**Page 24**: Check one checkbox ticked for every label group
**Page 27**: Name of Entity, Address of Tax Residence, City of Incorporation, Date of Incorporation, PAN
**Page 28–29**: Checkbox validations (condition based)
**Page 53**: First Applicant: Name, PAN, DOB, Contact Address, City, Pincode, State, Country, Email, Mobile, Income Tax Slab/Networth, Occupation Details, Place of Birth, Mode of Holding
**Page 54**: Bank Mandate 1: Name of Bank, Branch, A/C No, Account Type, IFSC, Bank Address
**Page 55**: Pan, Date of Incorporation, Name, Address Type, Place of Incorporation, Country of Incorporation, Net Worth INR, Net Worth Date.

---

#### 3. Private Limited Non-Individual Account Opening Form

- **Page 5**: PAN, Name, Date of Incorporation, Place of Incorporation, Date of Commencement, Registration Number, Entity Type, Registered Address: Line 1, City, District, Pin Code, State, Country
- **Page 6**: Correspondence Address, Mobile, Email ID, Related Persons, Date, Place
- **Page 8**: Name, Maiden Name, Father /Spouse’s Name, Mother Name, Date of Birth, Gender, Nationality, Related Person Type, A – Aadhaar Card, Correspondence/Local Address
- **Page 9**: Permanent residence address of applicant, if different from above A / Overseas Address, A – Aadhaar Card, Mobile, Email ID, Date, Place
- **Page 11**: Name, Maiden Name, Father /Spouse’s Name, Mother Name, Date of Birth, Gender, Nationality, Related Person Type, A – Aadhaar Card, Correspondence/Local Address
- **Page 12**: Permanent residence address of applicant, if different from above A / Overseas Address, A – Aadhaar Card, Mobile, Email ID, Date, Place
- **Page 14**: Type of Account -Sub Status, Gross annual income range p.a., Occupation, Please tick if applicable
- **Page 15**: Additional Details, Past Actions
- **Page 16**: Bank Proof Submitted, Account Type, Bank Name, Bank Account No, Branch Address, IFSC Code, MICR No
- **Page 18**: Check one checkbox ticked for every label group
- **Page 22**: Name of Client/First Holder, Address of Client, Trading Account No, DPID CDSL, Demat Account No.
- **Page 24**: Check one checkbox ticked for every label group
- **Page 25**: Check one checkbox ticked for every label group
- **Page 30**: Name of the entity, Customer ID, Address of tax residence, Address Type, Country of incorporation, City of incorporation, Entity Constitution Type, Date of Incorporation, PAN, Identification type and Identification Number, Issuing country for identification number provided in, Please tick the applicable tax resident declaration
- **Page 56**: Broker/Agent Code ARN:, EUIN, Name of the First Applicant, PAN Number, KYC, Date Of Birth, Contact Address, City, Pincode, State, Country, Email, Mobile, Income Tax Slab/Networth, Occupation Details, Place of Birth, Country of Tax Residence, Politically exposed person / Related to Politically exposed person etc.?, Mode of Holding, Bank Mandate 1 Details: Name of Bank, Branch, A/C No, A/C Type, IFSC Code, Bank Address
- **Page 58**: Pan, Date of Incorporation, Name, Address Type, Place of Incorporation, Country of Incorporation, Gross Annual Income Details in INR, Net Worth in INR in Lacs, Is “Entity” a tax resident of any country other than India

---

#### 4. LLP Non-Individual Account Opening Form

- **Page 5**: PAN, Name, Date of Incorporation, Place of Incorporation, Date of Commencement, Registration Number, Entity Type, Registered Address: Line 1, City, District, Pin Code, State, Country
- **Page 6**: Correspondence Address, Mobile, Email ID, Related Persons, Date, Place
- **Page 8**: Name, Maiden Name, Father /Spouse’s Name, Mother Name, Date of Birth, Gender, Nationality, Related Person Type, A – Aadhaar Card, Correspondence/Local Address
- **Page 9**: Permanent residence address of applicant, if different from above A / Overseas Address, A – Aadhaar Card, Mobile, Email ID, Date, Place
- **Page 11**: Name, Maiden Name, Father /Spouse’s Name, Mother Name, Date of Birth, Gender, Nationality, Related Person Type, A – Aadhaar Card, Correspondence/Local Address
- **Page 12**: Permanent residence address of applicant, if different from above A / Overseas Address, A – Aadhaar Card, Mobile, Email ID, Date, Place
- **Page 14**: Type of Account -Sub Status, Gross annual income range p.a., Occupation, Please tick if applicable
- **Page 15**: Additional Details, Past Actions
- **Page 16**: Bank Proof Submitted, Account Type, Bank Name, Bank Account No, Branch Address, IFSC Code, MICR No
- **Page 18**: Check one checkbox ticked for every label group
- **Page 22**: Name of Client/First Holder, Address of Client, Trading Account No, DPID CDSL, Demat Account No.
- **Page 24**: Check one checkbox ticked for every label group
- **Page 25**: Check one checkbox ticked for every label group
- **Page 30**: Name of the entity, Customer ID, Address of tax residence, Address Type, Country of incorporation, City of incorporation, Entity Constitution Type, Date of Incorporation, PAN, Identification type and Identification Number, Issuing country for identification number provided in, Please tick the applicable tax resident declaration
- **Page 56**: Broker/Agent Code ARN:, EUIN, Name of the First Applicant, PAN Number, KYC, Date Of Birth, Contact Address, City, Pincode, State, Country, Email, Mobile, Income Tax Slab/Networth, Occupation Details, Place of Birth, Country of Tax Residence, Politically exposed person / Related to Politically exposed person etc.?, Mode of Holding
- **Page 57**: Bank Mandate 1 Details: Name of Bank, Branch, A/C No, A/C Type, IFSC Code, Bank Address
- **Page 58**: Pan, Date of Incorporation, Name, Address Type, Place of Incorporation, Country of Incorporation, Gross Annual Income Details in INR, Net Worth in INR in Lacs, Is “Entity” a tax resident of any country other than India

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
  "checkbox_validation": [
    {
      "page_number": <Page>,
      "status": "Passed" | "Failed"
    }
  ],
  "aadhaar_masking_status": "Masked" | "Unmasked",
  "Final_status": "Passed" | "Failed"
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