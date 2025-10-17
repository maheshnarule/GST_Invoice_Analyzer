# 🧾 GST_Invoice_Analyzer

The **GST Invoice Analyzer** is an **AI-powered web application** designed to streamline invoice processing for **businesses, Chartered Accountants (CAs), and tax professionals**.  
It simplifies GST compliance and accounting workflows by leveraging automation and AI-based document understanding.

---

## 🚀 Key Features

- **📂 Multi-Invoice Extraction:**  
  Extract structured data from multiple invoice files (PDFs or images) using AI.

- **📊 Table View & Analytics:**  
  View and analyze extracted invoice data in organized, interactive tables.

- **🧮 Bill Generation:**  
  Create professional tax invoices with automatic **HSN & GST lookup**.

---

## ⚙️ Installation & Setup

# Step 1: Prerequisites Setup

# 🐍 Install Python 3.8+
- Download from [python.org](https://www.python.org/downloads/)
- Verify installation:
  ```bash
  python --version

# Get Google API Key

-Visit Google AI Studio
-Create an API key for Gemini AI
-Save the key securely for use in the application

# Step 2: Application Setup

Extract all project files into a folder.

Create a .env file in the project root directory and add your API key:

GOOGLE_API_KEY=your_google_api_key_here


Initialize Database

# Create database and tables (user and items)
python user_db_setup.py

# Upload CSV file of items & HSN numbers to items table
python upload_csv_to_db.py


Install Dependencies

pip install -r requirements.txt

Step 3: Launch Application

Run the following command to start the application:

streamlit run main_app.py


Once launched, the app will open automatically in your default browser at:
👉 http://localhost:8501

# Technologies Used

Python

Streamlit (Web UI)

SQLite/MySQL (Database)

Gemini AI API (Invoice Data Extraction)

Pandas / OpenPyXL (Data Handling)

pdfplumber / PyTesseract / EasyOCR (PDF & OCR Processing)
