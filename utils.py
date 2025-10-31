import pdfplumber
import re

def parse_pdf(pdf_path):
    transactions = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                found_table = False
                for table in tables:
                    if table:
                        found_table = True
                        for row in table[1:]:
                            if not row:
                                continue
                            # handle variable-length rows
                            if len(row) >= 4:
                                date = row[0].strip() if row[0] else ''
                                particulars = row[1].strip() if row[1] else ''
                                debit = row[2].strip() if row[2] else '0'
                                credit = row[3].strip() if row[3] else '0'
                                try:
                                    if debit and debit != '0':
                                        amount = -float(debit.replace(',', ''))
                                    elif credit and credit != '0':
                                        amount = float(credit.replace(',', ''))
                                    else:
                                        continue
                                except Exception:
                                    continue
                                transactions.append({
                                    'date': date,
                                    'description': particulars,
                                    'amount': amount
                                })
                if not found_table:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                            if match:
                                date, desc, amount = match.groups()
                                amount_clean = float(amount.replace(',', ''))
                                transactions.append({
                                    'date': date,
                                    'description': desc.strip(),
                                    'amount': amount_clean
                                })
    except Exception:
        pass
    return transactions

def categorize_transaction(description):
    desc_lower = (description or '').lower()
    if any(keyword in desc_lower for keyword in ['swiggy', 'zomato', 'food', 'restaurant', 'cafe', 'dominos', 'pizza', "kfc"]):
        return 'Food & Dining'
    elif any(keyword in desc_lower for keyword in ['bigbasket', 'dmart', 'grocery', 'supermarket', 'reliance fresh', 'bigbasket']):
        return 'Groceries'
    elif any(keyword in desc_lower for keyword in ['uber', 'ola', 'taxi', 'transport', 'rapido', 'auto', 'redbus']):
        return 'Transportation'
    elif any(keyword in desc_lower for keyword in ['amazon', 'flipkart', 'shopping', 'myntra', 'ajio']):
        return 'Shopping'
    elif any(keyword in desc_lower for keyword in ['recharge', 'bill', 'electricity', 'water', 'gas', 'broadband', 'internet']):
        return 'Bills & Utilities'
    elif any(keyword in desc_lower for keyword in ['netflix', 'prime', 'hotstar', 'movie', 'entertainment']):
        return 'Entertainment'
    elif any(keyword in desc_lower for keyword in ['pharmacy', 'medical', 'health', 'apollo', 'max']):
        return 'Health & Medical'
    elif any(keyword in desc_lower for keyword in ['irctc', 'train', 'flight', 'travel', 'booking']):
        return 'Travel'
    elif any(keyword in desc_lower for keyword in ['atm', 'cash', 'withdraw']):
        return 'Cash Withdrawal'
    elif any(keyword in desc_lower for keyword in ['salary', 'income', 'credit']):
        return 'Income'
    else:
        return 'Others'
