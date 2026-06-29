from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=4)
    elements.append(Paragraph("Hospital Management System", title_style))
    elements.append(Paragraph(f"Invoice: {invoice.invoice_number}", styles['Heading2']))
    elements.append(Spacer(1, 10))

    patient = invoice.patient
    info_data = [
        ["Patient", patient.full_name, "Date", invoice.created_at.strftime('%d %b %Y')],
        ["Patient ID", patient.patient_id, "Status", invoice.get_status_display()],
        ["Phone", patient.phone, "", ""],
    ]
    info_table = Table(info_data, colWidths=[80, 160, 80, 140])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # Line items
    data = [["Description", "Type", "Amount (₹)"]]
    for item in invoice.items.all():
        data.append([item.description, item.get_item_type_display(), f"{item.amount:.2f}"])
    data.append(["", "Total", f"{invoice.total_amount:.2f}"])
    data.append(["", "Paid", f"{invoice.amount_paid:.2f}"])
    data.append(["", "Balance Due", f"{invoice.balance_due:.2f}"])

    table = Table(data, colWidths=[260, 120, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    if invoice.payments.exists():
        elements.append(Paragraph("Payment History", styles['Heading3']))
        pay_data = [["Transaction ID", "Mode", "Amount (₹)", "Date"]]
        for p in invoice.payments.all():
            pay_data.append([p.transaction_id, p.get_mode_display(), f"{p.amount:.2f}", p.paid_at.strftime('%d %b %Y %H:%M')])
        pay_table = Table(pay_data, colWidths=[140, 80, 90, 140])
        pay_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ]))
        elements.append(pay_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
