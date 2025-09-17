from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from config import Config
from flask_migrate import Migrate  # Thêm dòng này


app = Flask(__name__)
app.config.from_object(Config)


# Import db from models to avoid circular import
from models import db
db.init_app(app)
migrate = Migrate(app, db)  # Thêm dòng này sau khi db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Custom template filters
@app.template_filter('format_currency')
def format_currency(value):
    """Format number as Vietnamese currency"""
    if value is None:
        return "0 ₫"
    try:
        return f"{int(value):,} ₫"
    except (ValueError, TypeError):
        return "0 ₫"

# Import routes after db initialization
from routes import auth, employees, attendance, payroll, payments, reports

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(employees.bp)
app.register_blueprint(attendance.bp)
app.register_blueprint(payroll.bp)
app.register_blueprint(payments.bp)
app.register_blueprint(reports.bp)

@app.route('/')
@login_required
def index():
    # Import models here to avoid circular import
    from models import Employee, Attendance, Payroll, Payment, Department
    
    # Get current date info
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Employee statistics
    total_employees = Employee.query.filter_by(is_active=True).count()
    new_employees_this_month = Employee.query.filter(
        db.extract('month', Employee.hire_date) == current_month,
        db.extract('year', Employee.hire_date) == current_year
    ).count()
    
    # Department statistics
    total_departments = Department.query.count()
    
    # Attendance statistics for current month
    current_month_attendance = Attendance.query.filter(
        db.extract('month', Attendance.date) == current_month,
        db.extract('year', Attendance.date) == current_year
    ).all()
    
    total_work_hours = sum(a.total_hours or 0 for a in current_month_attendance)
    total_overtime_hours = sum(a.overtime_hours or 0 for a in current_month_attendance)
    attendance_records = len(current_month_attendance)
    
    # Payroll statistics for current month
    current_month_payroll = Payroll.query.filter_by(
        month=current_month, 
        year=current_year
    ).all()
    
    total_salary = sum(p.total_salary for p in current_month_payroll)
    total_allowances = sum(p.allowance for p in current_month_payroll)
    total_deductions = sum(p.deductions for p in current_month_payroll)
    total_overtime_pay = sum(p.overtime_pay for p in current_month_payroll)
    
    # Payment statistics for current month
    # Get payments for current month by checking payment_date
    current_month_payments = Payment.query.filter(
        db.extract('month', Payment.payment_date) == current_month,
        db.extract('year', Payment.payment_date) == current_year
    ).all()
    
    total_payments = sum(p.amount for p in current_month_payments if p.status == 'completed')
    pending_payments = sum(p.amount for p in current_month_payments if p.status == 'pending')
    failed_payments = sum(p.amount for p in current_month_payments if p.status == 'failed')
    
    # Calculate average salary
    if total_employees > 0:
        avg_salary = total_salary / total_employees
    else:
        avg_salary = 0
    
    # Recent activities (last 5 records)
    recent_attendances = Attendance.query.order_by(Attendance.date.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()
    
    # Department distribution
    departments = Department.query.all()
    dept_stats = []
    for dept in departments:
        emp_count = Employee.query.filter_by(department_id=dept.id, is_active=True).count()
        if emp_count > 0:
            dept_salary = sum(emp.salary for emp in Employee.query.filter_by(department_id=dept.id, is_active=True).all())
            dept_stats.append({
                'name': dept.name,
                'count': emp_count,
                'total_salary': dept_salary
            })
    
    # Monthly trends (last 6 months)
    monthly_trends = []
    for i in range(6):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((i + 1) // 12)
        
        month_attendance = Attendance.query.filter(
            db.extract('month', Attendance.date) == month,
            db.extract('year', Attendance.date) == year
        ).count()
        
        month_payroll = Payroll.query.filter_by(month=month, year=year).all()
        month_salary = sum(p.total_salary for p in month_payroll)
        
        monthly_trends.append({
            'month': month,
            'year': year,
            'attendance': month_attendance,
            'salary': month_salary
        })
    
    monthly_trends.reverse()
    
    return render_template('dashboard.html',
                         # Employee stats
                         total_employees=total_employees,
                         new_employees_this_month=new_employees_this_month,
                         total_departments=total_departments,
                         
                         # Attendance stats
                         total_work_hours=total_work_hours,
                         total_overtime_hours=total_overtime_hours,
                         attendance_records=attendance_records,
                         
                         # Payroll stats
                         total_salary=total_salary,
                         total_allowances=total_allowances,
                         total_deductions=total_deductions,
                         total_overtime_pay=total_overtime_pay,
                         avg_salary=avg_salary,
                         
                         # Payment stats
                         total_payments=total_payments,
                         pending_payments=pending_payments,
                         failed_payments=failed_payments,
                         
                         # Current month/year
                         current_month=current_month,
                         current_year=current_year,
                         
                         # Recent activities
                         recent_attendances=recent_attendances,
                         recent_payments=recent_payments,
                         
                         # Department distribution
                         dept_stats=dept_stats,
                         
                         # Monthly trends
                         monthly_trends=monthly_trends)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)
