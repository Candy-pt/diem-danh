from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, Department, Position
from datetime import datetime

bp = Blueprint('employees', __name__, url_prefix='/employees')

@bp.route('/')
@login_required
def index():
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('employees/index.html', employees=employees)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        try:
            employee = Employee(
                employee_id=request.form.get('employee_id'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                position=request.form.get('position'),
                department=request.form.get('department'),
                hire_date=datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date(),
                salary=float(request.form.get('salary')),
                allowance=float(request.form.get('allowance', 0))
            )
            
            db.session.add(employee)
            db.session.commit()
            
            flash('Employee created successfully!', 'success')
            return redirect(url_for('employees.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating employee: {str(e)}', 'error')
    
    departments = Department.query.all()
    positions = Position.query.all()
    return render_template('employees/create.html', departments=departments, positions=positions)

@bp.route('/<int:id>')
@login_required
def show(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/show.html', employee=employee)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            employee.employee_id = request.form.get('employee_id')
            employee.first_name = request.form.get('first_name')
            employee.last_name = request.form.get('last_name')
            employee.email = request.form.get('email')
            employee.phone = request.form.get('phone')
            employee.address = request.form.get('address')
            employee.position = request.form.get('position')
            employee.department = request.form.get('department')
            employee.hire_date = datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date()
            employee.salary = float(request.form.get('salary'))
            employee.allowance = float(request.form.get('allowance', 0))
            employee.is_active = 'is_active' in request.form
            employee.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees.show', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'error')
    
    departments = Department.query.all()
    positions = Position.query.all()
    return render_template('employees/edit.html', employee=employee, departments=departments, positions=positions)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    employee = Employee.query.get_or_404(id)
    
    try:
        employee.is_active = False
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {str(e)}', 'error')
    
    return redirect(url_for('employees.index'))

@bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_api(id):
    employee = Employee.query.get_or_404(id)
    
    try:
        employee.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Employee deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/employees')
@login_required
def api_employees():
    employees = Employee.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': emp.id,
        'employee_id': emp.employee_id,
        'name': f"{emp.first_name} {emp.last_name}",
        'email': emp.email,
        'position': emp.position,
        'department': emp.department,
        'salary': emp.salary
    } for emp in employees])
