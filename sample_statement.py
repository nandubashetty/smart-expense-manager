from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'PhonePe Statement', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()
pdf.set_font('Arial', '', 10)
pdf.cell(0, 10, 'Transaction History', 0, 1)
pdf.ln(5)

pdf.set_font('Arial', 'B', 10)
pdf.cell(30, 10, 'Date', 1)
pdf.cell(80, 10, 'Particulars', 1)
pdf.cell(30, 10, 'Debit', 1)
pdf.cell(30, 10, 'Credit', 1)
pdf.cell(30, 10, 'Balance', 1)
pdf.ln()

pdf.set_font('Arial', '', 10)
transactions = [
    ("15/10/2023", "Swiggy Order - Pizza", "150.00", "", "5000.00"),
    ("16/10/2023", "BigBasket Groceries", "500.00", "", "4500.00"),
    ("17/10/2023", "Ola Ride to Office", "120.00", "", "4380.00"),
    ("18/10/2023", "Amazon Shopping", "2000.00", "", "2380.00")
]

for date, particulars, debit, credit, balance in transactions:
    pdf.cell(30, 10, date, 1)
    pdf.cell(80, 10, particulars, 1)
    pdf.cell(30, 10, debit, 1)
    pdf.cell(30, 10, credit, 1)
    pdf.cell(30, 10, balance, 1)
    pdf.ln()

pdf.output('sample_statement.pdf')
