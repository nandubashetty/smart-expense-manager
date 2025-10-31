from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from utils import parse_pdf, categorize_transaction

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///phonepe_analyzer.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    monthly_limit = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50))
    description = db.Column(db.String(500))
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide username and password')
            return redirect(url_for('register'))
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username already exists. Choose another.')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.lower().endswith('.pdf'):
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            transactions = parse_pdf(filename)
            for trans in transactions:
                category = categorize_transaction(trans.get('description',''))
                new_trans = Transaction(
                    user_id=current_user.id,
                    date=trans.get('date',''),
                    description=trans.get('description',''),
                    amount=trans.get('amount',0.0),
                    category=category
                )
                db.session.add(new_trans)
            db.session.commit()
            flash('File uploaded and processed successfully!')
            return redirect(url_for('dashboard'))
        flash('Invalid file type. Please upload a PDF.')
    return render_template('upload.html')

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    date = request.form.get('date')
    description = request.form.get('description')
    try:
        amount = float(request.form.get('amount'))
    except (ValueError, TypeError):
        flash('Invalid amount provided')
        return redirect(url_for('dashboard'))
    category = request.form.get('category')
    new_trans = Transaction(
        user_id=current_user.id,
        date=date,
        description=description,
        amount=-abs(amount),
        category=category
    )
    db.session.add(new_trans)
    db.session.commit()
    flash('Expense added successfully!')
    return redirect(url_for('dashboard'))

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        transaction.date = request.form.get('date')
        transaction.description = request.form.get('description')
        try:
            transaction.amount = float(request.form.get('amount'))
        except (ValueError, TypeError):
            flash('Invalid amount')
            return redirect(url_for('edit_expense', id=id))
        transaction.category = request.form.get('category')
        db.session.commit()
        flash('Expense updated successfully!')
        return redirect(url_for('dashboard'))
    return render_template('edit_expense.html', transaction=transaction)

@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))
    db.session.delete(transaction)
    db.session.commit()
    flash('Expense deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        monthly_limit = request.form.get('monthly_limit')
        try:
            limit_value = float(monthly_limit)
            if limit_value < 0:
                flash('Monthly limit must be a non-negative number!')
            else:
                current_user.monthly_limit = limit_value
                db.session.commit()
                flash('Monthly limit updated successfully!')
                return redirect(url_for('dashboard'))
        except (ValueError, TypeError):
            flash('Please enter a valid number!')
    return render_template('settings.html', user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime

    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()
    categories = {}
    date_wise = {}
    total_expenses = 0.0
    current_month_expenses = 0.0

    current_date = datetime.now()
    current_month = current_date.strftime('%m')
    current_year = current_date.strftime('%Y')

    for trans in transactions:
        categories.setdefault(trans.category or 'Others', 0.0)
        categories[trans.category or 'Others'] += abs(trans.amount or 0.0)
        if trans.amount is not None and trans.amount < 0:
            total_expenses += abs(trans.amount)
            date_wise.setdefault(trans.date or '', 0.0)
            date_wise[trans.date or ''] += abs(trans.amount)
            try:
                if '/' in (trans.date or ''):
                    parts = (trans.date or '').split('/')
                    if len(parts) >= 3:
                        trans_month = parts[1]
                        trans_year = parts[2]
                        if trans_month == current_month and trans_year == current_year:
                            current_month_expenses += abs(trans.amount)
            except Exception:
                pass

    date_wise = dict(sorted(date_wise.items()))

    monthly_limit = float(current_user.monthly_limit or 0.0)
    remaining_budget = monthly_limit - current_month_expenses if monthly_limit > 0 else 0.0
    limit_percentage = (current_month_expenses / monthly_limit * 100) if monthly_limit > 0 else 0.0

    if limit_percentage >= 90:
        limit_status = 'danger'
    elif limit_percentage >= 70:
        limit_status = 'warning'
    else:
        limit_status = 'success'

    return render_template('dashboard.html',
                         categories=categories,
                         date_wise=date_wise,
                         transactions=transactions,
                         total_expenses=total_expenses,
                         monthly_limit=monthly_limit,
                         current_month_expenses=current_month_expenses,
                         remaining_budget=remaining_budget,
                         limit_percentage=limit_percentage,
                         limit_status=limit_status)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
