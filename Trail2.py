from mistralai import Mistral

api_key = "SJtWzHbiHf53ptPHd2ygPHYFZslvz76u"
client = Mistral(api_key=api_key)

# URL = input("Copy URL for PDF from your Application and paste here.")
# pdf_url = URL

# Give Message and Document you want to extract data for
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": """
You are an intelligent assistant for validating financial account opening documents. You will receive a PDF document for one of the following account types:

1. Trading and Demat Account Opening Form - Resident Individual/NRI
2. Trading and Demat Account Opening Form – Non-individual
3. Neo Yield Enhancer - Discretionary Portfolio Management Services (DPMS)
4. *– Non-Discretionary Portfolio Management Service (NDPMS)

---

### TASKS:

1. **Detect the account type** based on form heading in the PDF.

2. **Extract the mandatory fields** listed below based on the account type and page number.

3. **Validate**:
   - All fields must be filled (not blank, missing, or placeholder like "____").
   - Aadhaar number must be **masked** – only last 4 digits should be visible (e.g., XXXX-XXXX-1234).
   - On pages with checkbox-based questions, **at least one checkbox must be selected per label group**.
   - ✅ **Nominee** and **Second/Third Holder** fields are **optional**:
    - If values are present, validate them.
    - If all values are blank or the section is clearly marked "Opted Out", **do not fail the test**—assume the user has opted out.
 Based on the detected account type, extract ONLY the fields relevant to that type (page-wise).

✅ DO NOT use fields from other account types.
✅ DO NOT hallucinate field labels that are not explicitly shown in the document.
✅ DO NOT repeat the same field over and over again.


---

### MANDATORY FIELD STRUCTURE:

#### 1. Trading and Demat Account Opening Form - Resident Individual/NRI

- **Page 1**: Client Name, Account Opening Date, Form
- **Page 4**: Application Number, Application Type, KYC Mode, PAN, Name, Father/Spouse’s Name, Mother Name, Date of Birth, Gender, Marital Status, Nationality, Residential Status, A - Aadhaar Card, Correspondence Address: Line 1, City, District, Pin Code, State, Country, Address Type
- **Page 5**: Permanent Address: Line 1, City, District, Pin Code, State, Country, Address Type, A - Aadhaar Card, Mobile, Email ID, Date, Place
- **Page 10**: Type of Account - Sub Status, Gross Annual Income Range, Occupation, Trading Experience, Checkbox selection required
- **Page 12**: Sole / First Holder Name, PAN No., UID No., Second Holder Name, PAN No., UID No., Bank Proof Submitted, Account Type, Bank Name, Account Number, Branch Address, IFSC, MICR
- **Pages 13, 36, 37, 39**: Ensure at least one checkbox ticked per label group
- **Page 14**: Client Name, Date
- **Page 17**: First Holder Name, Second Holder Name, Date
- **Page 34**: Name of Client/First Holder, Address of Client, Depository Participant Name
- **Page 53**: Name, PAN, Father’s Name, Aadhaar, Nationality, City/Country of Birth, Tax Residence Address, Address Type, Tax Declaration, Name, Date, Place
- **Pages 60–61**: Full details of First & Second Applicant including Income/Net Worth, Contact, and Bank Mandate

---

#### 2. Trading and Demat Account Opening Form – Non-individual

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

#### 3. Neo Yield Enhancer - Discretionary Portfolio Management Services (DPMS)

- **Pages 9, 12**: Application Type, Account Type, KYC Number, Name, Father/Spouse’s Name, Mother Name, Date of Birth, PAN, Gender, Marital Status, Residential Status, Occupation, Aadhaar (masked), Address Line 1, City, District, State, Country, Pin Code, State/U.T. Code, Country Code, Address Type
- **Pages 10, 13**: Aadhaar, Address: Line 1, City, District, State, Country, Pin, State/U.T. Code, Country Code, Address Type, Mobile, Email
- **Page 29**: Applicant details (same as above) + Second Holder info
- **Pages 31–32**: FATCA/PEP: PAN, Name, Place of Birth, Income, PEP status, Tax residency
- **Pages 39–40**: Ensure at least one checkbox ticked per label group
- **Page 42**: Scheme Name, Client Declaration
- **Page 51**: Account Name, Account No, Bank Name, Branch, IFSC, Account Type, Bank Account Details, DP Name, Client ID, DP ID, Investment Experience, Risk Tolerance, Investment Horizon
- **Page 52**: Mode of Operation
- **Page 69**: Nominee Name, Address, Phone Number
- **Page 79**: Nominee/Guardian Name, Address, PAN, % Allocation

---

#### 4. Moderately Portfolio – Non-Discretionary Portfolio Management Service (NDPMS)

- **Page 2**: Application No., Client Name, Distributor Name, RM Name, Branch Name
- **Pages 10, 13, 16**: Application Type, Account Type, Name, Father/Spouse’s Name, Mother Name, DOB, Gender, Marital Status, Residential Status, Occupation, Aadhaar (masked), Address Line 1, City, District, State, Country, Pin Code, State/U.T. Code, Country Code, Address Type
- **Pages 11, 14, 17**: Same address and contact details + Mobile, Email ID
- **Page 30**: Applicant info (as above), Second Holder Details
- **Page 31**: Second Holder: Name, Gender, DOB, Nationality, PEP, Aadhaar (masked)
- **Pages 32–34**: FATCA + Tax Residency: PAN, Name, Place of Birth, Income, Occupation, Tax Country
- **Pages 40–41**: Ensure at least one checkbox ticked per label group
- **Page 52**: Bank Mandate: Account Name, Account No., Bank Name, Branch, IFSC, Account Type
- **Page 81**: Nominee/Guardian: Name, Address, PAN, Allocation %

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
  "overall_status": "Passed" | "Failed"
}

Be strict in validation. Any missing, blank, or incorrectly masked value should mark the field as "Test Failed" also give reason why test failed.
Only respond in the structured JSON format provided above.
"""
            },
            {
                "type": "document_url",
                "document_url":
                    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/Non-Individual/Typeone/Pdf/5836/NEO000005836-TradingDemat.pdf"
                    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/NeoWealthPOA/Pdf/3967/NEO000003967-TradingDemat.pdf" #--pass
                    "https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/5652/NEO000005652-NYE-DPMS.pdf" #--pass
                    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/5814/NEO000005814-NYE-DPMS.pdf" #--Pass
                    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/3713/NEO000003713-CONSERVATIVE-PORTFOLIO-NDPMS.pdf" #--pass
                    #"https://startuat.theneoworld.com/ClientDocuments//Businesswise/TypeEight/Pdf/4299/NEO000004299-MODERATELY-PORTFOLIO-NDPMS.pdf" #--pass
            },
        ],
    }
]
chat_response = client.chat.complete(
    model="mistral-small-latest",
    messages=messages,
)

# Print the Processed Data
print(chat_response.choices[0].message.content)