import os
import json # Still used for printing data in testing if needed

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle as RLParagraphStyle, getSampleStyleSheet # Renamed to avoid conflict
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


def get_business_details(is_customer=False):
    """Prompts the user for business details."""
    name = input("Enter Name: ")
    address = input("Enter Address: ")
    contact_details = input("Enter Contact Details: ")
    details = {
        "name": name,
        "address": address,
        "contact_details": contact_details,
    }
    if not is_customer:
        logo_path_input = input("Enter Logo Path (optional): ").strip()
        if logo_path_input:
            logo_path = logo_path_input
            while True:
                if os.path.exists(logo_path):
                    details["logo_path"] = logo_path
                    break
                else:
                    print(f"Warning: Logo file not found at '{logo_path}'")
                    new_input = input("Enter new logo path, or type 'skip' to continue without a logo: ").strip()
                    if new_input.lower() == 'skip':
                        logo_path = "" # Or None, if preferred downstream
                        break
                    else:
                        logo_path = new_input
            # If loop was exited by 'skip', logo_path might be empty, so only add if non-empty
            if logo_path: # This check is somewhat redundant if "" means no logo, but explicit.
                 details["logo_path"] = logo_path
            # If user skipped and logo_path is "", it won't be added to details if we only add non-empty paths.
            # Current logic: if logo_path_input was provided, we try to validate. If skipped, details["logo_path"] might not be set.
            # This is fine as generate_invoice_pdf checks for key existence.

    return details

def get_invoice_metadata():
    """Prompts the user for invoice metadata."""
    invoice_number = input("Enter Invoice Number: ")
    invoice_date = input("Enter Invoice Date (YYYY-MM-DD): ")
    due_date = input("Enter Due Date (YYYY-MM-DD): ")
    payment_terms = input("Enter Payment Terms: ")
    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "payment_terms": payment_terms,
    }

def get_line_items():
    """Prompts the user for line items."""
    line_items = []
    while True:
        add_item = input("Add a line item? (yes/no): ").lower()
        if add_item != "yes":
            break
        description = input("Enter item description: ")
        while True:
            try:
                quantity = float(input("Enter quantity: "))
                break
            except ValueError:
                print("Invalid input. Please enter a number for quantity.")
        while True:
            try:
                unit_price = float(input("Enter unit price: "))
                break
            except ValueError:
                print("Invalid input. Please enter a number for unit price.")
        line_items.append({
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
        })
    return line_items

def get_tax_details():
    """Prompts the user for tax details."""
    while True:
        try:
            # Expecting a dictionary like {"rate": 10.0} as per later updates
            rate_str = input("Enter tax rate (e.g., 10 for 10%): ")
            rate = float(rate_str)
            return {"rate": rate} # Store as dict
        except ValueError:
            print("Invalid input. Please enter a number for the tax rate.")

def collect_invoice_data():
    """Collects all invoice data from the user."""
    print("--- Enter Your Business Information ---")
    your_business = get_business_details()
    print("\n--- Enter Customer's Business Information ---")
    customer_business = get_business_details(is_customer=True)
    print("\n--- Enter Invoice Metadata ---")
    metadata = get_invoice_metadata() # Changed variable name
    print("\n--- Enter Line Items ---")
    line_items = get_line_items()
    print("\n--- Enter Tax Details ---")
    tax_details = get_tax_details()

    return {
        "your_business": your_business,
        "customer": customer_business,
        "metadata": metadata, # Changed key name
        "line_items": line_items,
        "tax_details": tax_details,
    }


def generate_invoice_pdf(data, filename):
    """Generates the invoice PDF document."""
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=1*inch, rightMargin=1*inch,
                            topMargin=1*inch, bottomMargin=1*inch)
    story = []

    # Define Paragraph Styles & Colors
    styles = getSampleStyleSheet() # Using getSampleStyleSheet for base styles

    base_font = 'Helvetica'
    base_font_bold = 'Helvetica-Bold'
    light_grey_color = colors.Color(0.9, 0.9, 0.9) # Lighter grey for background/lines
    medium_grey_color = colors.Color(0.7, 0.7, 0.7) # For less prominent lines

    styles.add(RLParagraphStyle(name='Normal_Custom', parent=styles['Normal'], fontName=base_font, fontSize=10, spaceAfter=4, leading=14))
    styles.add(RLParagraphStyle(name='Title_Custom', parent=styles['h1'], fontName=base_font_bold, fontSize=22, alignment=1, spaceAfter=0.3*inch, textColor=colors.darkblue))
    styles.add(RLParagraphStyle(name='BusinessName_Custom', parent=styles['Normal'], fontName=base_font_bold, fontSize=13, spaceAfter=4, leading=14))
    styles.add(RLParagraphStyle(name='AddressText_Custom', parent=styles['Normal'], fontName=base_font, fontSize=9, leading=12, spaceAfter=2, textColor=colors.darkslategray))
    styles.add(RLParagraphStyle(name='SectionHeader_Custom', parent=styles['h2'], fontName=base_font_bold, fontSize=11, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.darkblue))
    styles.add(RLParagraphStyle(name='Footer_Custom', parent=styles['Normal'], fontName=base_font, alignment=1, fontSize=8, textColor=colors.grey))


    # Invoice Title
    story.append(Paragraph("INVOICE", styles['Title_Custom']))
    story.append(Spacer(1, 0.1*inch))

    # Business and Customer Info Side-by-Side
    your_business_info_flowables = []
    if 'logo_path' in data['your_business'] and data['your_business']['logo_path'] and \
       os.path.exists(data['your_business']['logo_path']):
        try:
            img_reader = ImageReader(data['your_business']['logo_path'])
            img_width, img_height = img_reader.getSize()
            aspect_ratio = img_height / float(img_width) if img_width else 1
            display_width = 1.5 * inch
            display_height = display_width * aspect_ratio

            max_logo_height = 1.0 * inch
            if display_height > max_logo_height:
                display_height = max_logo_height
                display_width = display_height / aspect_ratio if aspect_ratio else display_width

            logo_img = Image(data['your_business']['logo_path'], width=display_width, height=display_height)
            your_business_info_flowables.append(logo_img)
            your_business_info_flowables.append(Spacer(1, 0.1*inch))
        except Exception as e:
            print(f"Error processing logo '{data['your_business']['logo_path']}': {e}")

    your_business_info_flowables.append(Paragraph(data['your_business']['name'].upper(), styles['BusinessName_Custom']))
    your_business_info_flowables.append(Paragraph(data['your_business']['address'].replace('\n', '<br/>'), styles['AddressText_Custom']))
    your_business_info_flowables.append(Paragraph(data['your_business']['contact_details'].replace('\n', '<br/>'), styles['AddressText_Custom']))

    customer_info_flowables = [
        Paragraph("BILL TO:", styles['SectionHeader_Custom']),
        Paragraph(data['customer']['name'].upper(), styles['BusinessName_Custom']),
        Paragraph(data['customer']['address'].replace('\n', '<br/>'), styles['AddressText_Custom']),
        Paragraph(data['customer']['contact_details'].replace('\n', '<br/>'), styles['AddressText_Custom']),
    ]

    available_width = A4[0] - (2 * inch)
    col_width_business = available_width * 0.55
    col_width_customer = available_width * 0.45

    business_customer_table_data = [[your_business_info_flowables, customer_info_flowables]]
    business_customer_table = Table(business_customer_table_data, colWidths=[col_width_business, col_width_customer])
    business_customer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(business_customer_table)
    story.append(Spacer(1, 0.2*inch))

    # Invoice Metadata - using a small table for alignment
    meta_data_table_list = [
        [Paragraph("<b>Invoice Number:</b>", styles['Normal_Custom']), Paragraph(data['metadata']['invoice_number'], styles['Normal_Custom'])],
        [Paragraph("<b>Invoice Date:</b>", styles['Normal_Custom']), Paragraph(data['metadata']['invoice_date'], styles['Normal_Custom'])],
        [Paragraph("<b>Due Date:</b>", styles['Normal_Custom']), Paragraph(data['metadata']['due_date'], styles['Normal_Custom'])],
    ]
    meta_table = Table(meta_data_table_list, colWidths=[1.2*inch, None])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.1*inch))

    # Payment Terms
    story.append(Paragraph("<b>PAYMENT TERMS:</b>", styles['SectionHeader_Custom']))
    payment_terms_text = data['metadata']['payment_terms'].replace('\n', '<br/>')
    story.append(Paragraph(payment_terms_text, styles['Normal_Custom']))
    story.append(Spacer(1, 0.2*inch))

    # Line Items Table
    line_items = data.get('line_items', [])
    if line_items:
        table_data_list = [['#', 'Item Description', 'Qty', 'Unit Price', 'Total']]
        for idx, item in enumerate(line_items):
            try:
                quantity_val = float(item['quantity'])
                unit_price_val = float(item['unit_price'])
                line_total_val = quantity_val * unit_price_val

                qty_str = f"{quantity_val:g}"

                table_data_list.append([
                    str(idx + 1),
                    Paragraph(item['description'], styles['Normal_Custom']),
                    qty_str,
                    f"{unit_price_val:.2f}",
                    f"{line_total_val:.2f}"
                ])
            except ValueError:
                print(f"Warning: Skipping line item due to invalid quantity/price: {item}")
                table_data_list.append([
                    str(idx + 1),
                    Paragraph(f"{item['description']} (Error: Invalid data)", styles['Normal_Custom']),
                    "N/A", "N/A", "N/A"
                ])

        col_widths = [0.3*inch, 3.2*inch, 0.6*inch, 1.0*inch, 1.2*inch]
        invoice_items_table = Table(table_data_list, colWidths=col_widths, repeatRows=1)

        item_table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), light_grey_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.darkslategray),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), base_font_bold),
            ('FONTSIZE', (0,0), (-1,0), 9),

            ('LINEBELOW', (0,0), (-1,0), 1, colors.darkslategray),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, medium_grey_color),
            ('LINEAFTER', (0,0), (-2, -1), 0.5, medium_grey_color),

            ('ALIGN', (0,1), (0,-1), 'CENTER'),
            ('ALIGN', (1,1), (1,-1), 'LEFT'),
            ('ALIGN', (2,1), (2,-1), 'CENTER'),
            ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

            ('TOPPADDING', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,1), (-1,-1), 5),
            ('BOTTOMPADDING', (0,1), (-1,-1), 5)
        ])
        invoice_items_table.setStyle(item_table_style)
        story.append(invoice_items_table)
        story.append(Spacer(1, 0.2*inch))

    # Calculate Totals
    line_items_data = data.get('line_items', [])
    subtotal = sum(float(item.get('quantity', 0)) * float(item.get('unit_price', 0)) for item in line_items_data)

    tax_info_from_data = data.get('tax_details', {})
    tax_rate_percentage = 0.0
    if isinstance(tax_info_from_data, dict):
        tax_rate_percentage = float(tax_info_from_data.get('rate', 0.0))
    elif isinstance(tax_info_from_data, (float, int)):
        tax_rate_percentage = float(tax_info_from_data)

    tax_amount = subtotal * (tax_rate_percentage / 100.0)
    grand_total = subtotal + tax_amount

    # Totals Table
    totals_data_list = [
        ['Subtotal:', f"{subtotal:.2f}"],
        [f"Tax ({tax_rate_percentage:.2f}%):", f"{tax_amount:.2f}"],
        ['Grand Total:', f"{grand_total:.2f}"]
    ]

    usable_width = A4[0] - doc.leftMargin - doc.rightMargin
    totals_val_col_width = 1.5 * inch
    totals_desc_col_width = usable_width - totals_val_col_width - (0.05*inch)

    totals_table = Table(totals_data_list, colWidths=[totals_desc_col_width, totals_val_col_width])

    totals_table_style = TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), base_font),
        ('FONTSIZE', (0,0), (-1,-1), 9),

        ('FONTNAME', (0,2), (1,2), base_font_bold),
        ('FONTSIZE', (0,2), (1,2), 10),

        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),

        ('LINEBELOW', (0,0), (1,0), 0.5, medium_grey_color),
        ('LINEBELOW', (0,1), (1,1), 0.5, medium_grey_color),

        ('TOPPADDING', (0,2), (1,2), 5),
        ('BOTTOMPADDING', (0,2), (1,2), 5),
        ('BACKGROUND', (0,2), (1,2), light_grey_color),
        ('TEXTCOLOR', (0,2), (1,2), colors.darkslategray)
    ])
    totals_table.setStyle(totals_table_style)
    story.append(totals_table)
    story.append(Spacer(1, 0.2*inch))

    # Simple Footer
    story.append(Paragraph("Thank you for your business! We appreciate your prompt payment.", styles['Footer_Custom']))

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF {filename}: {e}")
        raise


if __name__ == "__main__":
    print("Invoice Generator Initialized")
    print("Starting invoice data collection...")

    invoice_data = collect_invoice_data()

    output_filename_prompt = "Enter the filename for the PDF (e.g., invoice.pdf, default: invoice_output.pdf): "
    user_filename = input(output_filename_prompt).strip()

    if not user_filename:
        output_filename = "invoice_output.pdf"
    else:
        if not user_filename.lower().endswith(".pdf"):
            output_filename = user_filename + ".pdf"
        else:
            output_filename = user_filename

    try:
        print(f"\nGenerating PDF: {output_filename}...")
        generate_invoice_pdf(invoice_data, output_filename)
        print(f"Invoice successfully generated: {output_filename}")
    except Exception as e:
        print(f"Error during PDF generation: {e}")
