
import os
import warnings
import logging
import streamlit as st
import tempfile
import requests
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import json
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import pandas as pd
from datetime import datetime
import re
import random
import sqlite3

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv

# Configuration
load_dotenv()
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)

# ==================== DATABASE FUNCTIONS ====================
def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect("database.db")

def get_all_categories():
    """Get all categories from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def get_items_by_category(category):
    """Get items by category from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, hsn_code, rate_of_gst FROM items WHERE category = ? ORDER BY item_name", (category,))
        items = cursor.fetchall()
        conn.close()
        return items
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def get_item_details(item_name):
    """Get HSN code and GST rate for specific item"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT hsn_code, rate_of_gst FROM items WHERE item_name = ?", (item_name,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, None

# ==================== UTILITY FUNCTIONS ====================
def generate_invoice_number():
    """Generate random invoice number"""
    prefix = "INV"
    year = datetime.now().strftime("%Y")
    random_num = random.randint(1000, 9999)
    return f"{prefix}/{year}/{random_num}"

def generate_gstin():
    """Generate random GSTIN number"""
    state_code = str(random.randint(1, 37)).zfill(2)
    pan = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=10))
    entity_code = str(random.randint(1, 9))
    check_digit = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
    return f"{state_code}{pan}{entity_code}Z{check_digit}"

def calculate_summary_statistics(invoices):
    """Calculate summary statistics for invoices"""
    total_invoices = len(invoices)
    total_grand_total = sum(invoice.get('grand_total', 0) for invoice in invoices)
    total_gst_amount = sum(invoice.get('total_gst', 0) for invoice in invoices)
    total_taxable_amount = total_grand_total - total_gst_amount
    
    return {
        'total_invoices': total_invoices,
        'total_grand_total': total_grand_total,
        'total_gst_amount': total_gst_amount,
        'total_taxable_amount': total_taxable_amount
    }

# ==================== TABLE VIEW PAGE ====================
def table_view_page():
    st.header("📊 Table View - Extracted Invoice Data")
    st.markdown("View all extracted invoice data in an organized table format")
    
    # Check if we have extracted data
    if 'verified_invoices' not in st.session_state or not st.session_state.verified_invoices:
        st.warning("📝 No extracted invoice data found. Please extract data from invoices first using the 'Multi-Invoice Extraction' page.")
        st.info("Go to **Multi-Invoice Extraction** page to upload and extract data from invoice files.")
        return
    
    extracted_invoices = st.session_state.verified_invoices
    
    st.success(f"✅ Found {len(extracted_invoices)} extracted invoice(s)")
    
    # Display each invoice in an expandable section
    for i, invoice in enumerate(extracted_invoices):
        with st.expander(f"📄 {invoice.get('file_name', f'Invoice {i+1}')}", expanded=True):
            display_single_invoice_data(invoice, i+1)
    
    # Download options
    st.markdown("---")
    st.subheader("📥 Download All Extracted Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON Download - Enhanced with items and summary
        enhanced_json_data = prepare_enhanced_json_data(extracted_invoices)
        json_data = json.dumps(enhanced_json_data, indent=2)
        st.download_button(
            label="📄 Download JSON (Full Data)",
            data=json_data,
            file_name="all_extracted_invoices_with_items.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # CSV Download - Enhanced format with items and summary
        csv_data = prepare_enhanced_csv_data(extracted_invoices)
        csv_file = csv_data.to_csv(index=False)
        
        st.download_button(
            label="📊 Download CSV (Full Data)",
            data=csv_file,
            file_name="all_extracted_invoices_with_items.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Summary Statistics
    st.markdown("---")
    st.subheader("📈 Summary Statistics")
    display_summary_statistics(extracted_invoices)

def display_single_invoice_data(invoice, invoice_number):
    """Display data for a single invoice in an organized format with items table"""
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧔 Seller Information")
        seller_info_html = f"""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745;'>
            <p><strong>Seller Name:</strong> {invoice.get('seller_name', 'N/A')}</p>
            <p><strong>GSTIN:</strong> {invoice.get('gstin_no', 'N/A')}</p>
            <p><strong>Place:</strong> {invoice.get('place', 'N/A')}</p>
            <p><strong>State:</strong> {invoice.get('state', 'N/A')}</p>
        </div>
        """
        st.markdown(seller_info_html, unsafe_allow_html=True)
    
    with col2:
        st.subheader("👤 Customer Information")
        customer_info_html = f"""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #007bff;'>
            <p><strong>Customer Name:</strong> {invoice.get('customer_name', 'N/A')}</p>
            <p><strong>Invoice Date:</strong> {invoice.get('date', 'N/A')}</p>
            <p><strong>Invoice No:</strong> {invoice.get('invoice_no', 'N/A')}</p>
        </div>
        """
        st.markdown(customer_info_html, unsafe_allow_html=True)
    
    # Items Table Section
    st.markdown("---")
    st.subheader("📦 Invoice Items")
    
    if 'items' in invoice and invoice['items']:
        display_items_table(invoice['items'])
    else:
        st.info("No detailed item information available for this invoice.")
    
    # Financial Information
    st.markdown("---")
    st.subheader("💰 Financial Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Grand Total", 
            f"₹{invoice.get('grand_total', 0):,.2f}",
            help="Total amount including all taxes"
        )
    
    with col2:
        st.metric(
            "Total GST", 
            f"₹{invoice.get('total_gst', 0):,.2f}",
            help="Total GST amount calculated"
        )
    
    with col3:
        taxable_amount = invoice.get('grand_total', 0) - invoice.get('total_gst', 0)
        st.metric(
            "Taxable Amount", 
            f"₹{taxable_amount:,.2f}",
            help="Amount before GST"
        )
    
    # File Information
    st.markdown("---")
    st.subheader("📁 File Information")
    file_info_html = f"""
    <div style='background-color: #e9ecef; padding: 10px; border-radius: 5px;'>
        <p><strong>File Name:</strong> {invoice.get('file_name', 'N/A')}</p>
        <p><strong>Extraction Status:</strong> ✅ Verified</p>
    </div>
    """
    st.markdown(file_info_html, unsafe_allow_html=True)

def display_items_table(items):
    """Display items in a formatted table"""
    if not items:
        st.info("No items data available")
        return
    
    # Prepare display data
    display_data = []
    for i, item in enumerate(items):
        display_data.append({
            'Sr No': i + 1,
            'Item Name': item.get('item_name', 'N/A'),
            'HSN Code': item.get('hsn_code', 'N/A'),
            'Quantity': item.get('quantity', 'N/A'),
            'Unit Price': f"₹{item.get('unit_price', 0):.2f}",
            'Amount': f"₹{item.get('amount', 0):.2f}",
            'GST Rate': item.get('gst_rate', 'N/A')
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True)
    
    # Show items summary
    # (Items summary metrics removed as per requirements)

def display_summary_statistics(invoices):
    """Display summary statistics"""
    stats = calculate_summary_statistics(invoices)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Invoices", stats['total_invoices'])
    with col2:
        st.metric("Total Grand Total", f"₹{stats['total_grand_total']:,.2f}")
    with col3:
        st.metric("Total GST Amount", f"₹{stats['total_gst_amount']:,.2f}")
    with col4:
        st.metric("Total Taxable Amount", f"₹{stats['total_taxable_amount']:,.2f}")

def prepare_enhanced_json_data(invoices):
    """Prepare enhanced JSON data with all invoice and item information including summary"""
    enhanced_data = {
        'invoices': [],
        'summary_statistics': calculate_summary_statistics(invoices)
    }
    
    for invoice in invoices:
        invoice_data = {
            'file_name': invoice.get('file_name', ''),
            'invoice_number': invoice.get('invoice_no', ''),
            'invoice_date': invoice.get('date', ''),
            'seller_info': {
                'name': invoice.get('seller_name', ''),
                'gstin': invoice.get('gstin_no', ''),
                'place': invoice.get('place', ''),
                'state': invoice.get('state', '')
            },
            'customer_info': {
                'name': invoice.get('customer_name', ''),
            },
            'financial_summary': {
                'grand_total': invoice.get('grand_total', 0),
                'total_gst': invoice.get('total_gst', 0),
                'taxable_amount': invoice.get('grand_total', 0) - invoice.get('total_gst', 0)
            },
            'items': invoice.get('items', [])
        }
        enhanced_data['invoices'].append(invoice_data)
    
    return enhanced_data

def prepare_enhanced_csv_data(invoices):
    """Prepare enhanced CSV data with all invoice and item information including summary"""
    csv_rows = []
    
    for invoice in invoices:
        # Add main invoice row
        if 'items' in invoice and invoice['items']:
            for item in invoice['items']:
                csv_rows.append({
                    'File Name': invoice.get('file_name', ''),
                    'Invoice Number': invoice.get('invoice_no', ''),
                    'Invoice Date': invoice.get('date', ''),
                    'Seller Name': invoice.get('seller_name', ''),
                    'Seller GSTIN': invoice.get('gstin_no', ''),
                    'Seller Place': invoice.get('place', ''),
                    'Seller State': invoice.get('state', ''),
                    'Customer Name': invoice.get('customer_name', ''),
                    'Item Name': item.get('item_name', ''),
                    'Item Category': item.get('category', ''),
                    'HSN Code': item.get('hsn_code', ''),
                    'Quantity': item.get('quantity', ''),
                    'Unit Price': item.get('unit_price', ''),
                    'Item Amount': item.get('amount', ''),
                    'GST Rate': item.get('gst_rate', ''),
                    'Grand Total': invoice.get('grand_total', 0),
                    'Total GST': invoice.get('total_gst', 0),
                    'Taxable Amount': invoice.get('grand_total', 0) - invoice.get('total_gst', 0)
                })
        else:
            # If no items data, add a single row for the invoice
            csv_rows.append({
                'File Name': invoice.get('file_name', ''),
                'Invoice Number': invoice.get('invoice_no', ''),
                'Invoice Date': invoice.get('date', ''),
                'Seller Name': invoice.get('seller_name', ''),
                'Seller GSTIN': invoice.get('gstin_no', ''),
                'Seller Place': invoice.get('place', ''),
                'Seller State': invoice.get('state', ''),
                'Customer Name': invoice.get('customer_name', ''),
                'Item Name': 'N/A',
                'Item Category': 'N/A',
                'HSN Code': 'N/A',
                'Quantity': 'N/A',
                'Unit Price': 'N/A',
                'Item Amount': 'N/A',
                'GST Rate': 'N/A',
                'Grand Total': invoice.get('grand_total', 0),
                'Total GST': invoice.get('total_gst', 0),
                'Taxable Amount': invoice.get('grand_total', 0) - invoice.get('total_gst', 0)
            })
    
    # Create DataFrame
    df = pd.DataFrame(csv_rows)
    
    # Add summary statistics as additional rows
    stats = calculate_summary_statistics(invoices)
    
    # Create summary rows
    summary_rows = [
       {'File Name': 'SUMMARY STATISTICS', 'Invoice Number': '', 'Invoice Date': '', 'Seller Name': '', 
        'Seller GSTIN': '', 'Seller Place': '', 'Seller State': '', 'Customer Name': '', 
        'Item Name': '', 'Item Category': '', 'HSN Code': '', 'Quantity': '', 'Unit Price': '', 
        'Item Amount': '', 'GST Rate': '', 'Grand Total': '', 'Total GST': '', 
        'Taxable Amount': ''},
       {'File Name': f'Total Invoices: {stats["total_invoices"]}', 'Invoice Number': '', 'Invoice Date': '', 
        'Seller Name': '', 'Seller GSTIN': '', 'Seller Place': '', 'Seller State': '', 'Customer Name': '', 
        'Item Name': '', 'Item Category': '', 'HSN Code': '', 'Quantity': '', 'Unit Price': '', 
        'Item Amount': '', 'GST Rate': '', 'Grand Total': '', 'Total GST': '', 
        'Taxable Amount': ''},
       {'File Name': f'Total Grand Total: {stats["total_grand_total"]:,.2f}', 'Invoice Number': '', 
        'Invoice Date': '', 'Seller Name': '', 'Seller GSTIN': '', 'Seller Place': '', 'Seller State': '', 
        'Customer Name': '', 'Item Name': '', 'Item Category': '', 'HSN Code': '', 'Quantity': '', 
        'Unit Price': '', 'Item Amount': '', 'GST Rate': '', 'Grand Total': '', 'Total GST': '', 'Taxable Amount': ''},
       {'File Name': f'Total GST Amount: {stats["total_gst_amount"]:,.2f}', 'Invoice Number': '', 
        'Invoice Date': '', 'Seller Name': '', 'Seller GSTIN': '', 'Seller Place': '', 'Seller State': '', 
        'Customer Name': '', 'Item Name': '', 'Item Category': '', 'HSN Code': '', 'Quantity': '', 
        'Unit Price': '', 'Item Amount': '', 'GST Rate': '', 'Grand Total': '', 'Total GST': '', 'Taxable Amount': ''},
       {'File Name': f'Total Taxable Amount: {stats["total_taxable_amount"]:,.2f}', 'Invoice Number': '', 
        'Invoice Date': '', 'Seller Name': '', 'Seller GSTIN': '', 'Seller Place': '', 'Seller State': '', 
        'Customer Name': '', 'Item Name': '', 'Item Category': '', 'HSN Code': '', 'Quantity': '', 
        'Unit Price': '', 'Item Amount': '', 'GST Rate': '', 'Grand Total': '', 'Total GST': '', 'Taxable Amount': ''}
    ]
    
    # Convert summary rows to DataFrame and concatenate
    summary_df = pd.DataFrame(summary_rows)
    final_df = pd.concat([df, summary_df], ignore_index=True)
    
    return final_df

# ==================== BILL GENERATION PAGE ====================
def bill_generation_page():
    st.header("🧾 Bill/Tax Invoice Generation")
    
    # Initialize session state for bill data
    if 'bill_items' not in st.session_state:
        st.session_state.bill_items = []
    if 'invoice_number' not in st.session_state:
        st.session_state.invoice_number = generate_invoice_number()
    if 'gstin_number' not in st.session_state:
        st.session_state.gstin_number = generate_gstin()
    
    # Invoice header section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Invoice Details")
        st.info(f"**Invoice No:** {st.session_state.invoice_number}")
        st.info(f"**GSTIN:** {st.session_state.gstin_number}")
        
        # Date input
        invoice_date = st.date_input("Invoice Date", datetime.now())
    
    with col2:
        st.subheader("Actions")
        if st.button("🔄 Generate New Invoice No"):
            st.session_state.invoice_number = generate_invoice_number()
            st.rerun()
        
        if st.button("🔄 Generate New GSTIN"):
            st.session_state.gstin_number = generate_gstin()
            st.rerun()
    
    st.markdown("---")
    
    # Seller and Buyer Information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧔 Seller Information")
        seller_name = st.text_input("Seller Name", placeholder="Enter seller name")
        seller_address = st.text_area("Seller Address", placeholder="Enter complete address")
        seller_contact = st.text_input("Contact Number", placeholder="Enter contact number")
        seller_bank = st.text_input("Bank Account Number", placeholder="Enter bank account number")
    
    with col2:
        st.subheader("👤 Buyer Information")
        buyer_name = st.text_input("Buyer Name", placeholder="Enter buyer name")
        buyer_address = st.text_area("Buyer Address", placeholder="Enter complete address")
        buyer_contact = st.text_input("Buyer Contact Number", placeholder="Enter contact number")
        buyer_gstin = st.text_input("Buyer GSTIN (Optional)", placeholder="Enter buyer GSTIN")
    
    st.markdown("---")
    
    # Item Addition Section
    st.subheader("📦 Add Items to Invoice")
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    
    with col1:
        categories = get_all_categories()
        selected_category = st.selectbox("Category", [""] + categories, key="category_select")
    
    with col2:
        items = []
        if selected_category:
            items_data = get_items_by_category(selected_category)
            items = [item[0] for item in items_data]
        selected_item = st.selectbox("Item", [""] + items, key="item_select")
    
    with col3:
        quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5, key="quantity_input")
    
    with col4:
        unit_price = st.number_input("Unit Price (₹)", min_value=0.0, value=0.0, step=0.01, key="price_input")
    
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add Item", use_container_width=True):
            if selected_item and quantity > 0 and unit_price > 0:
                # Get HSN code and GST rate from database
                hsn_code, gst_rate = get_item_details(selected_item)
                
                if hsn_code and gst_rate:
                    amount = quantity * unit_price
                    # Extract GST percentage from string (e.g., "5%" -> 5.0)
                    gst_percentage = float(gst_rate.strip('%'))
                    gst_amount = (amount * gst_percentage) / 100
                    
                    item_data = {
                        'category': selected_category,
                        'item_name': selected_item,
                        'hsn_code': hsn_code,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'amount': amount,
                        'gst_rate': gst_rate,
                        'gst_percentage': gst_percentage,
                        'gst_amount': gst_amount
                    }
                    
                    st.session_state.bill_items.append(item_data)
                    st.success(f"✅ {selected_item} added to invoice!")
                else:
                    st.error("❌ Could not fetch HSN code and GST rate for selected item")
            else:
                st.error("❌ Please fill all item details correctly")
    
    # Display current items in table
    if st.session_state.bill_items:
        st.markdown("---")
        st.subheader("📊 Current Invoice Items")
        
        # Prepare display data
        display_data = []
        for i, item in enumerate(st.session_state.bill_items):
            display_data.append({
                'Sr No': i + 1,
                'Item Name': item['item_name'],
                'HSN Code': item['hsn_code'],
                'Quantity': item['quantity'],
                'Unit Price': f"₹{item['unit_price']:.2f}",
                'Amount': f"₹{item['amount']:.2f}",
                'GST Rate': item['gst_rate']
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Calculate totals
        total_amount = sum(item['amount'] for item in st.session_state.bill_items)
        total_gst = sum(item['gst_amount'] for item in st.session_state.bill_items)
        grand_total = total_amount + total_gst
        
        # Display totals
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Amount", f"₹{total_amount:.2f}")
        with col2:
            st.metric("Total GST", f"₹{total_gst:.2f}")
        with col3:
            st.metric("Grand Total", f"₹{grand_total:.2f}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ Clear All Items", use_container_width=True):
                st.session_state.bill_items = []
                st.rerun()
        
        with col2:
            if st.button("💾 Save Invoice Draft", use_container_width=True):
                save_invoice_draft(seller_name, seller_address, seller_contact, seller_bank,
                                 buyer_name, buyer_address, buyer_contact, buyer_gstin,
                                 invoice_date, total_amount, total_gst, grand_total)
        
        with col3:
            if st.button("📄 Generate PDF Invoice", use_container_width=True, type="primary"):
                if seller_name and seller_address and buyer_name and buyer_address:
                    pdf_buffer = generate_pdf_invoice(
                        seller_name, seller_address, seller_contact, seller_bank,
                        buyer_name, buyer_address, buyer_contact, buyer_gstin,
                        invoice_date, total_amount, total_gst, grand_total
                    )
                    
                    # Download button for PDF
                    st.download_button(
                        label="📥 Download PDF Invoice",
                        data=pdf_buffer.getvalue(),
                        file_name=f"Invoice_{st.session_state.invoice_number.replace('/', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Please fill all required seller and buyer information")

def save_invoice_draft(seller_name, seller_address, seller_contact, seller_bank,
                      buyer_name, buyer_address, buyer_contact, buyer_gstin,
                      invoice_date, total_amount, total_gst, grand_total):
    """Save invoice draft to session state"""
    invoice_data = {
        'invoice_number': st.session_state.invoice_number,
        'gstin_number': st.session_state.gstin_number,
        'seller_info': {
            'name': seller_name,
            'address': seller_address,
            'contact': seller_contact,
            'bank_account': seller_bank
        },
        'buyer_info': {
            'name': buyer_name,
            'address': buyer_address,
            'contact': buyer_contact,
            'gstin': buyer_gstin
        },
        'invoice_date': invoice_date.strftime("%Y-%m-%d"),
        'items': st.session_state.bill_items,
        'totals': {
            'total_amount': total_amount,
            'total_gst': total_gst,
            'grand_total': grand_total
        }
    }
    
    st.session_state.invoice_draft = invoice_data
    st.success("✅ Invoice draft saved successfully!")

def generate_pdf_invoice(seller_name, seller_address, seller_contact, seller_bank,
                        buyer_name, buyer_address, buyer_contact, buyer_gstin,
                        invoice_date, total_amount, total_gst, grand_total):
    """Generate PDF invoice using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=30,
        alignment=1  # Center aligned
    )
    title = Paragraph("TAX INVOICE", title_style)
    story.append(title)
    
    # Invoice header table
    header_data = [
        ['Invoice Number:', st.session_state.invoice_number, 'Invoice Date:', invoice_date.strftime("%d-%m-%Y")],
        ['GSTIN:', st.session_state.gstin_number, 'Reverse Charge:', 'No']
    ]
    
    header_table = Table(header_data, colWidths=[100, 150, 100, 150])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Seller and Buyer information
    parties_data = [
        ['Details of Seller (Billed From)', 'Details of Buyer (Billed To)'],
        [f"{seller_name}\n{seller_address}\nContact: {seller_contact}\nBank: {seller_bank}", 
         f"{buyer_name}\n{buyer_address}\nContact: {buyer_contact}\nGSTIN: {buyer_gstin if buyer_gstin else 'Not Provided'}"]
    ]
    
    parties_table = Table(parties_data, colWidths=[250, 250])
    parties_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('FONT', (0, 1), (-1, 1), 'Helvetica', 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 20))
    
    # Items table
    items_header = ['Sr No', 'Item Description', 'HSN Code', 'Quantity', 'Unit Price', 'Amount', 'GST Rate']
    items_data = [items_header]
    
    for i, item in enumerate(st.session_state.bill_items):
        items_data.append([
            str(i + 1),
            f"{item['item_name']}",
            item['hsn_code'],
            str(item['quantity']),
            f"₹{item['unit_price']:.2f}",
            f"₹{item['amount']:.2f}",
            item['gst_rate']
        ])
    
    items_table = Table(items_data, colWidths=[30, 160, 60, 40, 60, 60, 60])
    items_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 7),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals table
    totals_data = [
        ['Total Amount:', f"₹{total_amount:.2f}"],
        ['Total GST:', f"₹{total_gst:.2f}"],
        ['Grand Total:', f"₹{grand_total:.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[100, 100])
    totals_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 10),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#FF6B6B')),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
    ]))
    story.append(totals_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    footer = Paragraph("This is a computer-generated invoice. No signature required.", footer_style)
    story.append(footer)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== MULTI-FILE TAX INVOICE EXTRACTION MODULE ====================
def multi_invoice_extraction_page():
    st.header("🧾 Multi-Invoice Data Extraction")
    st.markdown("Upload multiple tax invoices (PDF/Image) and extract structured data in batch")
    
    # Initialize session state for verified data
    if 'verified_invoices' not in st.session_state:
        st.session_state.verified_invoices = []
    if 'current_file_index' not in st.session_state:
        st.session_state.current_file_index = 0
    if 'extraction_complete' not in st.session_state:
        st.session_state.extraction_complete = False
    if 'show_final_table' not in st.session_state:
        st.session_state.show_final_table = False
    
    # File upload section for multiple files
    uploaded_invoices = st.file_uploader(
        "Upload Tax Invoices",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload multiple PDF or image files of your tax invoices",
        accept_multiple_files=True
    )
    
    # Add manual mode option
    manual_mode = st.checkbox("Enable Manual Verification Mode", 
                            help="Verify each invoice extraction manually before adding to table")
    
    if uploaded_invoices:
        st.success(f"📁 {len(uploaded_invoices)} file(s) uploaded successfully!")
        
        # Display file list
        with st.expander("📋 Uploaded Files", expanded=True):
            for i, file in enumerate(uploaded_invoices):
                status = "✅ Verified" if i < len(st.session_state.verified_invoices) else "⏳ Pending"
                st.write(f"{i+1}. {file.name} ({file.size} bytes) - {status}")
        
        # Store uploaded files in session state for preview
        st.session_state.uploaded_invoices_dict = {file.name: file for file in uploaded_invoices}
        st.session_state.all_uploaded_files = uploaded_invoices
        
        # Extraction button
        if st.button("🔍 Extract Data from All Invoices", type="primary"):
            st.session_state.verified_invoices = []
            st.session_state.current_file_index = 0
            st.session_state.extraction_complete = False
            st.session_state.show_final_table = False
            st.session_state.all_extracted_data = []
            
            with st.spinner(f"🤖 AI is analyzing {len(uploaded_invoices)} invoice(s)..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_invoices):
                    status_text.text(f"Processing {i+1}/{len(uploaded_invoices)}: {uploaded_file.name}")
                    
                    # Extract data from each file
                    extracted_data = extract_invoice_data(uploaded_file)
                    
                    if extracted_data:
                        # Add filename to extracted data
                        extracted_data["file_name"] = uploaded_file.name
                        st.session_state.all_extracted_data.append(extracted_data)
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_invoices))
                
                status_text.text("✅ Extraction completed!")
                st.session_state.extraction_complete = True
                
                if not st.session_state.all_extracted_data:
                    st.error("Failed to extract data from any invoices")
                    return
            
            # If manual mode is enabled, show verification interface
            if manual_mode and st.session_state.all_extracted_data:
                st.info("🔍 Manual Verification Mode Enabled - Please verify each invoice below")
            else:
                # If manual mode is disabled, show all data directly
                st.session_state.verified_invoices = st.session_state.all_extracted_data
                st.session_state.show_final_table = True
        
        # Show verification interface if manual mode is enabled
        if (manual_mode and 
            st.session_state.extraction_complete and 
            st.session_state.current_file_index < len(st.session_state.all_extracted_data)):
            show_manual_verification_interface()
        
        # Show current verified table rows as they are added
        if st.session_state.verified_invoices:
            display_current_table()
        
        # Show final table when all files are processed
        if (st.session_state.extraction_complete and 
            ((manual_mode and st.session_state.current_file_index >= len(st.session_state.all_extracted_data)) or
             (not manual_mode and st.session_state.verified_invoices))):
            st.session_state.show_final_table = True
        
        if st.session_state.show_final_table:
            display_final_table()

def show_manual_verification_interface():
    """Show manual verification interface for each file"""
    if (not st.session_state.all_extracted_data or 
        st.session_state.current_file_index >= len(st.session_state.all_extracted_data)):
        return
    
    current_data = st.session_state.all_extracted_data[st.session_state.current_file_index]
    current_file = current_data["file_name"]
    
    st.markdown("---")
    st.subheader(f"📄 Verification: {current_file} ({st.session_state.current_file_index + 1}/{len(st.session_state.all_extracted_data)})")
    
    # Show file preview
    show_file_preview(current_file)
    
    # Verification form
    with st.form(key=f"verification_form_{current_file}"):
        st.markdown("### Verify Extracted Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_no = st.text_input("Invoice Number", 
                                     value=current_data.get("invoice_no", ""),
                                     key=f"inv_no_{current_file}")
            gstin_no = st.text_input("GSTIN Number", 
                                   value=current_data.get("gstin_no", ""),
                                   key=f"gstin_{current_file}")
            seller_name = st.text_input("Seller Name", 
                                      value=current_data.get("seller_name", ""),
                                      key=f"seller_{current_file}")
            customer_name = st.text_input("Customer Name", 
                                        value=current_data.get("customer_name", ""),
                                        key=f"customer_{current_file}")
        
        with col2:
            grand_total = st.number_input("Grand Total", 
                                        value=float(current_data.get("grand_total", 0)),
                                        key=f"total_{current_file}")
            total_gst = st.number_input("Total GST", 
                                      value=float(current_data.get("total_gst", 0)),
                                      key=f"gst_{current_file}")
            place = st.text_input("Place", 
                                value=current_data.get("place", ""),
                                key=f"place_{current_file}")
            date = st.text_input("Date", 
                               value=current_data.get("date", ""),
                               key=f"date_{current_file}")
            state = st.text_input("State", 
                                value=current_data.get("state", ""),
                                key=f"state_{current_file}")
        
        # Items section for manual entry
        st.markdown("### 📦 Invoice Items")
        st.info("Add item details manually if available")
        
        items = current_data.get('items', [])
        if not items:
            items = [{}]  # Start with one empty item
        
        for i, item in enumerate(items):
            with st.expander(f"Item {i+1}", expanded=i==0):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    item_name = st.text_input(f"Item Name {i+1}", value=item.get('item_name', ''), key=f"item_name_{i}_{current_file}")
                with col2:
                    hsn_code = st.text_input(f"HSN Code {i+1}", value=item.get('hsn_code', ''), key=f"hsn_{i}_{current_file}")
                with col3:
                    quantity = st.number_input(f"Quantity {i+1}", value=float(item.get('quantity', 1)), key=f"qty_{i}_{current_file}")
                with col4:
                    unit_price = st.number_input(f"Unit Price {i+1}", value=float(item.get('unit_price', 0)), key=f"price_{i}_{current_file}")
        
        add_more_items = st.checkbox("Add more items", key=f"add_more_{current_file}")
        if add_more_items:
            new_item_count = st.number_input("Number of additional items", min_value=1, max_value=10, value=1, key=f"new_items_{current_file}")
        
        # Buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            verify_button = st.form_submit_button("✅ Verify & Add to Table")
        
        with col2:
            skip_button = st.form_submit_button("⏭️ Skip This File")
        
        with col3:
            if st.session_state.current_file_index > 0:
                previous_button = st.form_submit_button("⬅️ Previous File")
            else:
                previous_button = False
        
        if verify_button:
            # Create verified data entry with items
            verified_data = {
                "file_name": current_file,
                "invoice_no": invoice_no,
                "gstin_no": gstin_no,
                "seller_name": seller_name,
                "customer_name": customer_name,
                "grand_total": grand_total,
                "total_gst": total_gst,
                "place": place,
                "date": date,
                "state": state,
                "items": items  # Include items in verified data
            }
            
            st.session_state.verified_invoices.append(verified_data)
            st.session_state.current_file_index += 1
            st.rerun()
        
        elif skip_button:
            # Add skipped file with original data
            st.session_state.verified_invoices.append(current_data)
            st.session_state.current_file_index += 1
            st.rerun()
        
        elif previous_button:
            st.session_state.current_file_index -= 1
            if st.session_state.verified_invoices:
                st.session_state.verified_invoices.pop()
            st.rerun()

def show_file_preview(filename):
    """Show preview of the uploaded file"""
    if filename in st.session_state.uploaded_invoices_dict:
        preview_file = st.session_state.uploaded_invoices_dict[filename]
        
        if preview_file.type == "application/pdf":
            # For PDFs, show download option
            st.warning("PDF preview - Download the file to view complete document")
            st.download_button(
                label="📥 Download PDF",
                data=preview_file.getvalue(),
                file_name=filename,
                mime="application/pdf",
                key=f"download_{filename}"
            )
        else:
            # For images, display the image
            try:
                image = Image.open(preview_file)
                st.image(image, caption=f"Preview: {filename}", use_container_width=True)
            except Exception as e:
                st.error(f"Could not display image: {e}")

def display_current_table():
    """Display current verified table rows"""
    st.markdown("---")
    st.subheader("📊 Current Verified Data")
    
    if st.session_state.verified_invoices:
        # Prepare display data
        display_data = []
        for data in st.session_state.verified_invoices:
            display_data.append({
                "File Name": data.get("file_name", "N/A"),
                "Invoice No": data.get("invoice_no", "N/A"),
                "GSTIN No": data.get("gstin_no", "N/A"),
                "Seller Name": data.get("seller_name", "N/A"),
                "Customer Name": data.get("customer_name", "N/A"),
                "Grand Total": f"₹{data.get('grand_total', 0):.2f}" if data.get('grand_total') else "N/A",
                "Total GST": f"₹{data.get('total_gst', 0):.2f}" if data.get('total_gst') else "N/A",
                "Place": data.get("place", "N/A"),
                "Date": data.get("date", "N/A"),
                "State": data.get("state", "N/A"),
                "Items Count": len(data.get('items', []))
            })
        
        # Create DataFrame
        df = pd.DataFrame(display_data)
        
        # Display table
        st.dataframe(df, use_container_width=True)
        
        # Show progress
        total_files = len(st.session_state.all_uploaded_files)
        verified_count = len(st.session_state.verified_invoices)
        st.info(f"✅ {verified_count}/{total_files} files verified")

def display_final_table():
    """Display final extracted data table with download options"""
    st.markdown("---")
    st.subheader("🎉 Final Extracted Data Table")
    
    if not st.session_state.verified_invoices:
        st.warning("No verified data to display")
        return
    
    # Prepare data for display
    display_data = []
    for data in st.session_state.verified_invoices:
        display_data.append({
            "File Name": data.get("file_name", "N/A"),
            "Invoice No": data.get("invoice_no", "N/A"),
            "GSTIN No": data.get("gstin_no", "N/A"),
            "Seller Name": data.get("seller_name", "N/A"),
            "Customer Name": data.get("customer_name", "N/A"),
            "Grand Total": f"₹{data.get('grand_total', 0):.2f}" if data.get('grand_total') else "N/A",
            "Total GST": f"₹{data.get('total_gst', 0):.2f}" if data.get('total_gst') else "N/A",
            "Place": data.get("place", "N/A"),
            "Date": data.get("date", "N/A"),
            "State": data.get("state", "N/A"),
            "Items Count": len(data.get('items', []))
        })
    
    # Create DataFrame
    df = pd.DataFrame(display_data)
    
    # Display table
    st.dataframe(df, use_container_width=True)
    
    # Show file preview section
    st.subheader("📄 File Previews")
    selected_file = st.selectbox(
        "Select file to preview:",
        options=[data["file_name"] for data in st.session_state.verified_invoices],
        key="file_preview_selector"
    )
    
    if selected_file:
        preview_file = st.session_state.uploaded_invoices_dict[selected_file]
        st.write(f"**Previewing:** {selected_file}")
        
        if preview_file.type == "application/pdf":
            # For PDFs, show download option and info
            st.warning("PDF preview not available in this interface. Download the file to view.")
            st.download_button(
                label="📥 Download PDF",
                data=preview_file.getvalue(),
                file_name=selected_file,
                mime="application/pdf"
            )
        else:
            # For images, display the image
            try:
                image = Image.open(preview_file)
                st.image(image, caption=selected_file, use_container_width=True)
            except Exception as e:
                st.error(f"Could not display image: {e}")
    
    # Download options
    st.subheader("📥 Download Extracted Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON Download
        json_data = json.dumps(st.session_state.verified_invoices, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name="extracted_invoices_data.json",
            mime="application/json"
        )
    
    with col2:
        # CSV Download
        # Prepare clean CSV data without currency symbols
        csv_data = []
        for data in st.session_state.verified_invoices:
            csv_data.append({
                "file_name": data.get("file_name", ""),
                "invoice_no": data.get("invoice_no", ""),
                "gstin_no": data.get("gstin_no", ""),
                "seller_name": data.get("seller_name", ""),
                "customer_name": data.get("customer_name", ""),
                "grand_total": data.get("grand_total", ""),
                "total_gst": data.get("total_gst", ""),
                "place": data.get("place", ""),
                "date": data.get("date", ""),
                "state": data.get("state", "")
            })
        
        csv_df = pd.DataFrame(csv_data)
        csv_file = csv_df.to_csv(index=False)
        
        st.download_button(
            label="📊 Download CSV",
            data=csv_file,
            file_name="extracted_invoices_data.csv",
            mime="text/csv"
        )
    
    # Show completion message
    st.balloons()
    st.success(f"🎉 All {len(st.session_state.verified_invoices)} files have been processed successfully!")

def extract_invoice_data(uploaded_file):
    """Extract structured data from invoice using Gemini with enhanced validation"""
    try:
        # Save uploaded file temporarily with proper handling
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Create a more reliable temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            # Read the file content properly
            file_content = uploaded_file.getvalue()
            tmp.write(file_content)
            file_path = tmp.name
        
        # Reset file pointer for future use
        uploaded_file.seek(0)
        
        invoice_text = ""
        
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            try:
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                invoice_text = "\n".join([doc.page_content for doc in documents])
            except Exception as e:
                st.error(f"Error reading PDF {uploaded_file.name}: {e}")
                # Clean up temp file
                try:
                    os.unlink(file_path)
                except:
                    pass
                return None
        else:
            # Image OCR with much better error handling
            try:
                # First, verify the file exists and is readable
                if not os.path.exists(file_path):
                    st.error(f"Temporary file for {uploaded_file.name} was not created properly")
                    return None
                
                # Try multiple approaches to read the image
                try:
                    # Approach 1: Direct open with PIL
                    with Image.open(file_path) as img:
                        # Convert to RGB if necessary
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Save to a new temporary file to ensure format consistency
                        temp_jpg_path = file_path + "_processed.jpg"
                        img.save(temp_jpg_path, "JPEG", quality=95)
                        
                        # Read the processed image
                        with Image.open(temp_jpg_path) as processed_img:
                            invoice_text = pytesseract.image_to_string(processed_img)
                        
                        # Clean up temporary processed image
                        try:
                            os.unlink(temp_jpg_path)
                        except:
                            pass
                            
                except Exception as img_error:
                    # Approach 2: Try reading the original file directly
                    try:
                        invoice_text = pytesseract.image_to_string(file_path)
                    except Exception as direct_error:
                        # Approach 3: Last resort - read bytes and create image
                        try:
                            with open(file_path, 'rb') as f:
                                image_bytes = f.read()
                            image = Image.open(io.BytesIO(image_bytes))
                            invoice_text = pytesseract.image_to_string(image)
                        except Exception as bytes_error:
                            st.error(f"All image processing methods failed for {uploaded_file.name}: {bytes_error}")
                            return None
                        
            except Exception as e:
                st.error(f"Error processing image {uploaded_file.name}: {e}")
                # Clean up temp file
                try:
                    os.unlink(file_path)
                except:
                    pass
                return None
        
        # Clean up temp file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
        
        if not invoice_text.strip():
            st.warning(f"No text could be extracted from {uploaded_file.name}. The image might be blurry, contain no text, or be in an unsupported format.")
            return None
        
        # Prepare prompt for Gemini - Enhanced to extract items
        prompt = create_enhanced_extraction_prompt(invoice_text)
        
        # Initialize Gemini
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.1
        )
        
        # Get response from Gemini
        response = llm.invoke(prompt)
        
        extracted_json = parse_gemini_response(response.content)
        
        # Validate and clean extracted data
        if extracted_json:
            extracted_json = validate_extracted_data(extracted_json, invoice_text, uploaded_file.name)
        
        # Format date to YYYY.MM.DD if it exists
        if extracted_json and "date" in extracted_json:
            date_str = extracted_json.get("date", "")
            if date_str:
                formatted_date = format_date_to_ymd(date_str)
                extracted_json["date"] = formatted_date
        
        return extracted_json
        
    except Exception as e:
        st.error(f"Error during extraction of {uploaded_file.name}: {str(e)}")
        # Clean up any remaining temp files
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.unlink(file_path)
        except:
            pass
        return None

def create_enhanced_extraction_prompt(invoice_text):
    """Create enhanced prompt for multi-invoice extraction with items data"""
    
    prompt = f"""
    You are an expert at extracting structured data from Indian tax invoices. 
    Extract the following information from the invoice text below and return ONLY valid JSON format.
    
    CRITICAL INSTRUCTIONS FOR FIELD EXTRACTION:
    
    1. INVOICE NUMBER: Look for "Invoice No", "Invoice No.", "Invoice Number", "Bill No", "Bill Number", "Inv No"
    2. GSTIN NUMBER: Look for "GSTIN", "GSTIN No", "GST Number", "GSTIN/UIN". Format should be 15 characters like 27ABCDE1234F1Z5
    3. SELLER NAME: Look at the top of the invoice, usually the company name that issued the invoice
    4. CUSTOMER NAME: Look after "To:", "Bill To:", "Customer:", "M/s", "Mr.", or near the shipping/billing address
    5. GRAND TOTAL: Look for "Grand Total", "Total Amount", "Amount Payable", "Net Amount". Extract only the numerical value.
    6. TOTAL GST CALCULATION: This is VERY IMPORTANT. Calculate total GST using these methods:
       - Method A: Look for "Total GST", "Total Tax", "GST Total" 
       - Method B: Sum all "CGST" + "SGST" amounts
       - Method C: Sum all "IGST" amounts
       - Method D: Calculate from line items if GST breakdown is available
       - Method E: If GST amounts are shown separately, add them all
    7. PLACE: Look for city name in addresses. Usually after "Place of Supply", "Delivery At", or in seller/buyer address
    8. STATE: Extract the state from the address. Common states: Maharashtra, Karnataka, Tamil Nadu, Delhi, Uttar Pradesh, etc.
    9. DATE: Look for "Date", "Invoice Date", "Bill Date", "Date of Invoice". Format as DD-MM-YYYY or as shown.
    10. ITEMS: Extract line items with details like item name, quantity, unit price, amount, HSN code, GST rate
    
    GST CALCULATION EXAMPLES:
    - If you see: "CGST @9%: ₹155.59" and "SGST @9%: ₹155.59" then Total GST = 155.59 + 155.59 = 311.18
    - If you see: "IGST @18%: ₹381.36" then Total GST = 381.36
    - If you see GST breakdown like: "CGST 2.5%: ₹39.29, SGST 2.5%: ₹39.29, CGST 6%: ₹26.79, SGST 6%: ₹26.79, CGST 9%: ₹155.59, SGST 9%: ₹155.59" then Total GST = 39.29+39.29+26.79+26.79+155.59+155.59 = 443.34
    
    REQUIRED FIELDS:
    - invoice_no: Invoice number (text exactly as shown)
    - gstin_no: GSTIN number (15 characters format)
    - seller_name: Name of the seller/company
    - customer_name: Name of the customer/buyer  
    - grand_total: Total amount including taxes (number only, no symbols)
    - total_gst: Total GST amount (number only, calculate carefully)
    - place: Place of supply (city/town)
    - date: Invoice date (extract as is)
    - state: State name
    - items: Array of item objects with:
        - item_name: Name of the item
        - quantity: Quantity (number)
        - unit_price: Unit price (number)
        - amount: Total amount for this item (number)
        - hsn_code: HSN code if available
        - gst_rate: GST rate applied to this item
    
    IMPORTANT RULES: 
    - Return ONLY JSON, no additional text or explanations
    - For missing fields, use empty string "" or 0 for numbers or empty array [] for items
    - Extract dates exactly as they appear
    - Be very careful with invoice numbers - they often contain letters and numbers
    - For GST calculation: Be thorough and add ALL GST components (CGST+SGST or IGST)
    - For items: Try to extract as many line items as possible from the invoice
    
    INVOICE TEXT:
    {invoice_text}
    
    Return JSON in this exact format:
    {{
        "invoice_no": "string",
        "gstin_no": "string", 
        "seller_name": "string",
        "customer_name": "string",
        "grand_total": number,
        "total_gst": number,
        "place": "string",
        "date": "string",
        "state": "string",
        "items": [
            {{
                "item_name": "string",
                "quantity": number,
                "unit_price": number,
                "amount": number,
                "hsn_code": "string",
                "gst_rate": "string"
            }}
        ]
    }}
    """
    
    return prompt

def parse_gemini_response(response_text):
    """Parse Gemini response to extract JSON data"""
    try:
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # If no JSON found, try to parse the entire response
            return json.loads(response_text)
    except:
        # Basic cleaning for common issues
        cleaned = response_text.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(cleaned)
        except:
            st.error("Failed to parse AI response as JSON")
            return None

def validate_extracted_data(extracted_data, original_text, filename):
    """Validate and correct extracted data using fallback methods"""
    
    # Fallback extraction for critical fields
    if not extracted_data.get("invoice_no") or extracted_data.get("invoice_no") == "N/A":
        # Try direct pattern matching for invoice number
        invoice_patterns = [
            r'Invoice No\.?\s*:?\s*([A-Z0-9\-]+)',
            r'Invoice Number\s*:?\s*([A-Z0-9\-]+)',
            r'Bill No\.?\s*:?\s*([A-Z0-9\-]+)',
            r'INV-\s*([A-Z0-9\-]+)',
            r'Inv\.?\s*No\.?\s*:?\s*([A-Z0-9\-]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                extracted_data["invoice_no"] = match.group(1).strip()
                break
    
    # Fallback for GSTIN
    if not extracted_data.get("gstin_no") or extracted_data.get("gstin_no") == "N/A":
        gstin_pattern = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}'
        match = re.search(gstin_pattern, original_text)
        if match:
            extracted_data["gstin_no"] = match.group(0)
    
    # Fallback for grand total
    if not extracted_data.get("grand_total") or extracted_data.get("grand_total") == 0:
        total_patterns = [
            r'Grand Total\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)',
            r'Total Amount\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)',
            r'Amount Payable\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)',
            r'Net Amount\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    extracted_data["grand_total"] = float(amount_str)
                    break
                except ValueError:
                    continue
    
    # Fallback for total GST calculation
    if not extracted_data.get("total_gst") or extracted_data.get("total_gst") == 0:
        total_gst = calculate_total_gst_from_text(original_text)
        if total_gst > 0:
            extracted_data["total_gst"] = total_gst
    
    # Fallback for date
    if not extracted_data.get("date") or extracted_data.get("date") == "N/A":
        date_patterns = [
            r'Date\s*:?\s*(\d{2}-\d{2}-\d{4})',
            r'Date\s*:?\s*(\d{2}/\d{2}/\d{4})',
            r'Invoice Date\s*:?\s*(\d{2}-\d{2}-\d{4})',
            r'Bill Date\s*:?\s*(\d{2}-\d{2}-\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                extracted_data["date"] = match.group(1)
                break
    
    # Fallback for place and state
    if not extracted_data.get("place") or extracted_data.get("place") == "N/A":
        # Try to extract place from address
        place_patterns = [
            r'Place of Supply\s*:?\s*([A-Za-z\s]+)',
            r'Delivery At\s*:?\s*([A-Za-z\s]+)',
            r'City\s*:?\s*([A-Za-z\s]+)'
        ]
        for pattern in place_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                extracted_data["place"] = match.group(1).strip()
                break
    
    if not extracted_data.get("state") or extracted_data.get("state") == "N/A":
        # Common Indian states for pattern matching
        states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Delhi', 'Uttar Pradesh', 
                 'Gujarat', 'Rajasthan', 'Punjab', 'Haryana', 'Kerala', 'West Bengal',
                 'Andhra Pradesh', 'Telangana', 'Madhya Pradesh', 'Bihar', 'Odisha']
        
        for state in states:
            if state.lower() in original_text.lower():
                extracted_data["state"] = state
                break
    
    # Ensure items field exists
    if 'items' not in extracted_data:
        extracted_data['items'] = []
    
    return extracted_data

def calculate_total_gst_from_text(text):
    """Calculate total GST from invoice text using multiple methods"""
    total_gst = 0
    
    try:
        # Method 1: Look for explicit total GST
        total_gst_patterns = [
            r'Total GST\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)',
            r'Total Tax\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)',
            r'GST Total\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)'
        ]
        
        for pattern in total_gst_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = float(match.replace(',', ''))
                total_gst += amount
        
        if total_gst > 0:
            return total_gst
        
        # Method 2: Sum CGST and SGST amounts
        cgst_pattern = r'CGST\s*@?\s*[0-9.%]*\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)'
        sgst_pattern = r'SGST\s*@?\s*[0-9.%]*\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)'
        
        cgst_matches = re.findall(cgst_pattern, text, re.IGNORECASE)
        sgst_matches = re.findall(sgst_pattern, text, re.IGNORECASE)
        
        for match in cgst_matches:
            total_gst += float(match.replace(',', ''))
        for match in sgst_matches:
            total_gst += float(match.replace(',', ''))
        
        if total_gst > 0:
            return total_gst
        
        # Method 3: Sum IGST amounts
        igst_pattern = r'IGST\s*@?\s*[0-9.%]*\s*:?\s*[₹\s]*([0-9,]+\.?[0-9]*)'
        igst_matches = re.findall(igst_pattern, text, re.IGNORECASE)
        
        for match in igst_matches:
            total_gst += float(match.replace(',', ''))
        
    except Exception as e:
        st.warning(f"Error calculating GST: {e}")
    
    return total_gst

def format_date_to_ymd(date_str):
    """Convert various date formats to YYYY.MM.DD"""
    try:
        # Remove any extra spaces and common separators
        date_str = date_str.strip().replace('/', '-').replace('.', '-')
        
        # Month mapping for text months
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
            'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06',
            'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        # Try different date formats including text months
        formats_to_try = [
            # Standard formats
            '%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y',
            '%d.%m.%Y', '%d.%m.%y', '%Y.%m.%d',
            
            # Text month formats
            '%d-%b-%Y', '%d-%B-%Y', '%d %b %Y', '%d %B %Y',
            '%b-%d-%Y', '%B-%d-%Y', '%b %d, %Y', '%B %d, %Y',
            '%d-%b-%y', '%d-%B-%y', '%d %b %y', '%d %B %y',
        ]
        
        for fmt in formats_to_try:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y.%m.%d')
            except ValueError:
                continue
        
        # Special handling for "04-Mar-2020" type formats that might not be caught above
        try:
            # Try to manually parse text months
            date_lower = date_str.lower()
            for month_text, month_num in month_map.items():
                if month_text in date_lower:
                    # Extract day and year
                    parts = date_str.replace(',', ' ').replace('-', ' ').replace('/', ' ').split()
                    if len(parts) >= 3:
                        day = parts[0].zfill(2)
                        year = parts[2]
                        if len(year) == 2:  # Convert 2-digit year to 4-digit
                            year = '20' + year if int(year) <= 50 else '19' + year
                        return f"{year}.{month_num}.{day}"
        except:
            pass
        
        # If no format works, return original but try to clean it
        return date_str
    except:
        return date_str

# ==================== UPDATED MAIN APPLICATION ====================
def main():
    # App configuration
    st.set_page_config(
        page_title="Invoice Data Extractor",
        layout="wide",
        page_icon="🧾"
    )

    # CSS Styling
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', sans-serif;
        }
        section[data-testid="stSidebar"] {
            background-color: white;
            border-right: 2px solid #000000;
        }
        .main-header {
            color: #ffffff;
            font-weight: bold;
            text-align: center;
            background-color: #28a745;
            padding: 15px 0;
            border-bottom: 2px solid #2c3e50;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .stChatMessage {
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 8px;
        }
        .sidebar-button {
            background-color: #218838 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            border: 2px solid #555555 !important;
        }
        .sidebar-button:hover {
            background-color: #555555 !important;
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # App header
    st.markdown('<div class="main-header"><h1>🧾 GST Invoice Analyzer</h1></div>', unsafe_allow_html=True)
    st.caption("Extract structured data from multiple invoice files (PDF/Image) ")

    # Sidebar Navigation
    st.sidebar.header("🎯 Navigation")
    page = st.sidebar.selectbox(
        "Choose Mode",
        ["Multi-Invoice Extraction", "Table View", "Bill Generation"]
    )

    if page == "Multi-Invoice Extraction":
        multi_invoice_extraction_page()
    
    elif page == "Table View":
        table_view_page()
    
    elif page == "Bill Generation":
        bill_generation_page()

    # Features showcase
    with st.expander("🚀 Supported Features"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🧾 Multi-Invoice Extraction**")
            st.markdown("- Multiple PDF/Image invoices")
            st.markdown("- Batch processing")
            st.markdown("- Manual verification mode")
            st.markdown("- Real-time table updates")
            st.markdown("- CSV & JSON export")
        with col2:
            st.markdown("**📊 Table View**")
            st.markdown("- Organized invoice display")
            st.markdown("- Seller & customer info")
            st.markdown("- Item-level details")
            st.markdown("- Financial summaries")
            st.markdown("- Bulk downloads with items")
        with col3:
            st.markdown("**🧾 Bill Generation**")
            st.markdown("- Create tax invoices")
            st.markdown("- Database integration")
            st.markdown("- Automatic HSN/GST lookup")
            st.markdown("- PDF invoice generation")
            st.markdown("- Professional templates")

if __name__ == "__main__":
    main()