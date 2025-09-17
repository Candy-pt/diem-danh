from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required
from models import db, Employee, Attendance, Payroll, Payment, Department
from datetime import datetime, timedelta
import io
import csv
import json

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    """Reports dashboard"""
    # Get basic statistics
    total_employees = Employee.query.filter_by(is_active=True).count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    total_departments = Department.query.count()
    
    # Calculate average salary
    avg_salary = db.session.query(db.func.avg(Employee.salary)).scalar() or 0
    avg_salary = round(avg_salary / 1000000, 1)  # Convert to millions
    
    # Get current month/year
    now = datetime.now()
    current_month = now.strftime('%B %Y')
    
    # Get recent activities (placeholder)
    recent_activities = []
    
    return render_template('reports/index.html',
                         total_employees=total_employees,
                         active_employees=active_employees,
                         total_departments=total_departments,
                         avg_salary=avg_salary,
                         current_month=current_month,
                         recent_activities=recent_activities)

@bp.route('/employee')
@login_required
def employee_report():
    """Employee report"""
    employees = Employee.query.all()
    departments = Department.query.all()
    
    # Department statistics
    dept_stats = {}
    for dept in departments:
        dept_stats[dept.name] = Employee.query.filter_by(department=dept.name, is_active=True).count()
    
    return render_template('reports/employee.html',
                         employees=employees,
                         departments=departments,
                         dept_stats=dept_stats)

@bp.route('/attendance')
@login_required
def attendance_report():
    """Attendance report"""
    # Get date range from request
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get attendance records
    attendances = Attendance.query.filter(
        Attendance.date >= start_dt,
        Attendance.date <= end_dt
    ).all()
    
    # Calculate statistics
    total_days = (end_dt - start_dt).days + 1
    total_hours = sum(a.total_hours or 0 for a in attendances)
    total_overtime = sum(a.overtime_hours or 0 for a in attendances)
    
    return render_template('reports/attendance.html',
                         attendances=attendances,
                         start_date=start_date,
                         end_date=end_date,
                         total_days=total_days,
                         total_hours=total_hours,
                         total_overtime=total_overtime)

@bp.route('/payroll')
@login_required
def payroll_report():
    """Payroll report"""
    month = request.args.get('month', datetime.now().month)
    year = request.args.get('year', datetime.now().year)
    
    # Get payroll records for the month
    payrolls = Payroll.query.filter_by(month=month, year=year).all()
    
    # Calculate totals
    total_salary = sum(p.net_salary for p in payrolls)
    total_allowances = sum(p.allowances for p in payrolls)
    total_deductions = sum(p.deductions for p in payrolls)
    total_overtime = sum(p.overtime_pay for p in payrolls)
    
    return render_template('reports/payroll.html',
                         payrolls=payrolls,
                         month=month,
                         year=year,
                         total_salary=total_salary,
                         total_allowances=total_allowances,
                         total_deductions=total_deductions,
                         total_overtime=total_overtime)

@bp.route('/financial')
@login_required
def financial_report():
    """Financial report"""
    month = request.args.get('month', datetime.now().month)
    year = request.args.get('year', datetime.now().year)
    
    # Get payments for the month
    payments = Payment.query.filter_by(month=month, year=year).all()
    
    # Calculate statistics
    total_payments = sum(p.amount for p in payments if p.status == 'completed')
    pending_payments = sum(p.amount for p in payments if p.status == 'pending')
    failed_payments = sum(p.amount for p in payments if p.status == 'failed')
    
    # Payment method breakdown
    method_stats = {}
    for payment in payments:
        method = payment.payment_method
        if method not in method_stats:
            method_stats[method] = 0
        method_stats[method] += payment.amount
    
    return render_template('reports/financial.html',
                         payments=payments,
                         month=month,
                         year=year,
                         total_payments=total_payments,
                         pending_payments=pending_payments,
                         failed_payments=failed_payments,
                         method_stats=method_stats)

@bp.route('/monthly')
@login_required
def monthly_report():
    """Monthly comprehensive report"""
    month = request.args.get('month', datetime.now().month)
    year = request.args.get('year', datetime.now().year)
    
    # Get all data for the month
    employees = Employee.query.filter_by(is_active=True).all()
    attendances = Attendance.query.filter(
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).all()
    payrolls = Payroll.query.filter_by(month=month, year=year).all()
    payments = Payment.query.filter_by(month=month, year=year).all()
    
    return render_template('reports/monthly.html',
                         month=month,
                         year=year,
                         employees=employees,
                         attendances=attendances,
                         payrolls=payrolls,
                         payments=payments)

@bp.route('/export/excel')
@login_required
def export_excel():
    """Export data to Excel"""
    # This would typically use openpyxl or xlsxwriter
    # For now, return a placeholder
    return jsonify({'message': 'Excel export functionality will be implemented'})

@bp.route('/export/pdf')
@login_required
def export_pdf():
    """Export data to PDF"""
    # This would typically use reportlab or weasyprint
    # For now, return a placeholder
    return jsonify({'message': 'PDF export functionality will be implemented'})

@bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics"""
    # Get basic stats
    total_employees = Employee.query.filter_by(is_active=True).count()
    total_departments = Department.query.count()
    
    # Get monthly attendance data
    now = datetime.now()
    monthly_data = []
    for i in range(12):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((i + 1) // 12)
        
        attendances = Attendance.query.filter(
            db.extract('month', Attendance.date) == month,
            db.extract('year', Attendance.date) == year
        ).count()
        
        monthly_data.append({
            'month': month,
            'year': year,
            'attendance': attendances
        })
    
    monthly_data.reverse()
    
    return jsonify({
        'total_employees': total_employees,
        'total_departments': total_departments,
        'monthly_attendance': monthly_data
    })
