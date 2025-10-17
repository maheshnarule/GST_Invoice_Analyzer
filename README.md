# GST_Invoice_Analyzer
The GST Invoice Analyzer is an AI-powered web application designed to streamline invoice processing for businesses, Chartered Accountants (CAs), and tax professionals. The application provides three main functionalities:

-Multi-Invoice Extraction: Extract structured data from multiple invoice files (PDF/Images) using AI
-Table View & Analytics: View and analyze extracted invoice data in organized tables
-Bill Generation: Create professional tax invoices with automatic HSN/GST lookup


#Installation & Setup
Step 1: Prerequisites Setup
•	Install Python 3.8+
o	Download from python.org
o	Verify installation: python --version
•	Get Google API Key
o	Visit Google AI Studio
o	Create API key for Gemini AI
o	Save the API key securely
Step 2: Application Setup
•	Extract all project files to a folder
•	Create environment file (.env) in the project root:
GOOGLE_API_KEY=your_google_api_key_here
•	Initialize Database
// To create database and tables user and items in the database
      python user_db_setup.py 
//upload csv file of items & hsn no. in items table
      python upload_csv_to_db.py
•	Install Dependencies
     pip install -r requirements.txt
Step 3: Launch Application
     streamlit run main_app.py
The application will open in your default browser at http://localhost:8501
