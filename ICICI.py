from mistralai import Mistral
import json

# ✅ API Key
api_key = "SJtWzHbiHf53ptPHd2ygPHYFZslvz76u"

# ✅ Mistral client
client = Mistral(api_key=api_key)

# ✅ Document URL
document_url = "https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/4299/NEO000004299-ICICI.pdf"

# ✅ Message for validation
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
                "document_url": document_url
            }
        ]
    }
]

# ✅ Call the API
response = client.chat.complete(
    model="mistral-small-latest",
    messages=messages
)

# ✅ Output
result = response.choices[0].message.content
print(result)
