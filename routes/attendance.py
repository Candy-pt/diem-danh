from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Attendance, Employee
from datetime import datetime, date, timedelta
from sqlalchemy import and_
import qrcode
from io import BytesIO

bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@bp.route('/')
@login_required
def index():
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_employee = request.args.get('employee_id', '')
    
    query = Attendance.query.join(Employee)
    
    if selected_date:
        query = query.filter(Attendance.date == datetime.strptime(selected_date, '%Y-%m-%d').date())
    
    if selected_employee:
        query = query.filter(Attendance.employee_id == selected_employee)
    
    attendances = query.all()
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('attendance/index.html', 
                         attendances=attendances, 
                         employees=employees,
                         selected_date=selected_date,
                         selected_employee=selected_employee)

@bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    employee_id = request.form.get('employee_id')
    checkin_date = request.args.get('date', date.today().isoformat())
    check_in_time = datetime.now()
    
    # Check if already checked in today
    existing_attendance = Attendance.query.filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == checkin_date
        )
    ).first()
    
    if existing_attendance and existing_attendance.check_in:
        flash('Employee already checked in today!', 'error')
        return redirect(url_for('attendance.index'))
    
    if existing_attendance:
        existing_attendance.check_in = check_in_time
        existing_attendance.status = 'present'
    else:
        attendance = Attendance(
            employee_id=employee_id,
            date=checkin_date,
            check_in=check_in_time,
            status='present'
        )
        db.session.add(attendance)
    
    db.session.commit()
    flash('Check-in recorded successfully!', 'success'+ checkin_date)
    return redirect(url_for('attendance.index'))

@bp.route('/check-out', methods=['POST'])
@login_required
def check_out():
    employee_id = request.form.get('employee_id')
    check_out_time = datetime.now()
    
    attendance = Attendance.query.filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date == check_out_time.date()
        )
    ).first()
    
    if not attendance:
        flash('No check-in record found for today!', 'error')
        return redirect(url_for('attendance.index'))
    
    if attendance.check_out:
        flash('Employee already checked out today!', 'error')
        return redirect(url_for('attendance.index'))
    
    attendance.check_out = check_out_time
    
    # Calculate total hours and overtime
    if attendance.check_in:
        total_hours = (check_out_time - attendance.check_in).total_seconds() / 3600
        attendance.total_hours = round(total_hours, 2)
        
        # Calculate overtime (assuming 8 hours workday)
        if total_hours > 8:
            attendance.overtime_hours = round(total_hours - 8, 2)
    
    db.session.commit()
    flash('Check-out recorded successfully!', 'success')
    return redirect(url_for('attendance.index'))

@bp.route('/manual-entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    if request.method == 'POST':
        try:
            attendance = Attendance(
                employee_id=request.form.get('employee_id'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                check_in=datetime.strptime(request.form.get('check_in'), '%Y-%m-%d %H:%M') if request.form.get('check_in') else None,
                check_out=datetime.strptime(request.form.get('check_out'), '%Y-%m-%d %H:%M') if request.form.get('check_out') else None,
                status=request.form.get('status'),
                notes=request.form.get('notes')
            )
            
            # Calculate hours if both check-in and check-out are provided
            if attendance.check_in and attendance.check_out:
                total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
                attendance.total_hours = round(total_hours, 2)
                
                if total_hours > 8:
                    attendance.overtime_hours = round(total_hours - 8, 2)
            
            db.session.add(attendance)
            db.session.commit()
            
            flash('Attendance record created successfully!', 'success')
            return redirect(url_for('attendance.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating attendance record: {str(e)}', 'error')
    
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('attendance/manual_entry.html', employees=employees)

@bp.route('/report')
@login_required
def report():
    month = request.args.get('month', datetime.now().month)
    year = request.args.get('year', datetime.now().year)
    employee_id = request.args.get('employee_id', '')
    
    # Get attendance data for the month
    start_date = date(int(year), int(month), 1)
    if int(month) == 12:
        end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    
    query = Attendance.query.join(Employee).filter(
        and_(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
    )
    
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    
    attendances = query.all()
    employees = Employee.query.filter_by(is_active=True).all()
    
    # Calculate summary statistics
    total_working_days = len(set([a.date for a in attendances]))
    total_hours = sum([a.total_hours or 0 for a in attendances])
    total_overtime = sum([a.overtime_hours or 0 for a in attendances])
    
    return render_template('attendance/report.html',
                         attendances=attendances,
                         employees=employees,
                         month=month,
                         year=year,
                         employee_id=employee_id,
                         total_working_days=total_working_days,
                         total_hours=total_hours,
                         total_overtime=total_overtime)

@bp.route('/api/attendance/<int:employee_id>')
@login_required
def api_attendance(employee_id):
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    attendances = Attendance.query.filter(
        and_(
            Attendance.employee_id == employee_id,
            Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
            Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date()
        )
    ).all()
    
    return jsonify([{
        'date': att.date.strftime('%Y-%m-%d'),
        'check_in': att.check_in.strftime('%H:%M') if att.check_in else None,
        'check_out': att.check_out.strftime('%H:%M') if att.check_out else None,
        'total_hours': att.total_hours,
        'overtime_hours': att.overtime_hours,
        'status': att.status
    } for att in attendances])

@bp.route('/qr')
@login_required
def qr_code():
    today = date.today().isoformat()
    # Tạo URL điểm danh, ví dụ: /attendance/checkin?date=yyyy-mm-dd
    checkin_url = url_for('attendance.checkin', date=today, _external=True)
    # Tạo mã QR
    img = qrcode.make(checkin_url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@bp.route('/qr_screen')
def qr_screen():
    now = datetime.now()
    return render_template('attendance/qr_screen.html', now=now)


