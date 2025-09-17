#!/usr/bin/env python3
"""
Script khởi tạo cơ sở dữ liệu và dữ liệu mẫu cho hệ thống quản lý nhân sự trên Railway
"""

from app import app
from models import db, User, Employee, Department, Position, Attendance, Payroll, Payment
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import os
import random

def init_database():
    """Khởi tạo cơ sở dữ liệu"""
    with app.app_context():
        # Kiểm tra và tạo tất cả bảng
        db.create_all()
        print("✓ Đã tạo tất cả bảng trong cơ sở dữ liệu")

def create_sample_data():
    """Tạo dữ liệu mẫu"""
    with app.app_context():
        # Tạo user admin
        admin_user = User(
            username='admin',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        print("✓ Đã tạo tài khoản admin (username: admin, password: admin123)")

        # Tạo departments
        departments = [
            Department(name='Kỹ thuật', description='Phòng kỹ thuật và phát triển'),
            Department(name='Nhân sự', description='Phòng nhân sự và hành chính'),
            Department(name='Kinh doanh', description='Phòng kinh doanh và marketing'),
            Department(name='Tài chính', description='Phòng tài chính và kế toán'),
            Department(name='Vận hành', description='Phòng vận hành và sản xuất')
        ]
        
        for dept in departments:
            db.session.add(dept)
        print("✓ Đã tạo 5 phòng ban")

        # Tạo positions
        positions = [
            Position(title='Giám đốc', description='Giám đốc điều hành', base_salary=50000000),
            Position(title='Trưởng phòng', description='Trưởng phòng ban', base_salary=30000000),
            Position(title='Nhân viên cao cấp', description='Nhân viên có kinh nghiệm', base_salary=20000000),
            Position(title='Nhân viên', description='Nhân viên thường', base_salary=15000000),
            Position(title='Thực tập sinh', description='Thực tập sinh', base_salary=8000000)
        ]
        
        for pos in positions:
            db.session.add(pos)
        print("✓ Đã tạo 5 vị trí công việc")

        db.session.commit()

        # Tạo employees
        employees_data = [
            {
                'employee_id': 'NV001',
                'first_name': 'Nguyễn',
                'last_name': 'Văn A',
                'email': 'nguyenvana@company.com',
                'phone': '0901234567',
                'address': '123 Đường ABC, Quận 1, TP.HCM',
                'position': 'Giám đốc',
                'department': 'Kỹ thuật',
                'hire_date': date(2020, 1, 15),
                'salary': 50000000,
                'allowance': 5000000
            },
            {
                'employee_id': 'NV002',
                'first_name': 'Trần',
                'last_name': 'Thị B',
                'email': 'tranthib@company.com',
                'phone': '0901234568',
                'address': '456 Đường XYZ, Quận 2, TP.HCM',
                'position': 'Trưởng phòng',
                'department': 'Nhân sự',
                'hire_date': date(2021, 3, 20),
                'salary': 30000000,
                'allowance': 3000000
            },
            {
                'employee_id': 'NV003',
                'first_name': 'Lê',
                'last_name': 'Văn C',
                'email': 'levanc@company.com',
                'phone': '0901234569',
                'address': '789 Đường DEF, Quận 3, TP.HCM',
                'position': 'Nhân viên cao cấp',
                'department': 'Kinh doanh',
                'hire_date': date(2022, 6, 10),
                'salary': 20000000,
                'allowance': 2000000
            },
            {
                'employee_id': 'NV004',
                'first_name': 'Phạm',
                'last_name': 'Thị D',
                'email': 'phamthid@company.com',
                'phone': '0901234570',
                'address': '321 Đường GHI, Quận 4, TP.HCM',
                'position': 'Nhân viên',
                'department': 'Tài chính',
                'hire_date': date(2023, 1, 5),
                'salary': 15000000,
                'allowance': 1500000
            },
            {
                'employee_id': 'NV005',
                'first_name': 'Hoàng',
                'last_name': 'Văn E',
                'email': 'hoangvane@company.com',
                'phone': '0901234571',
                'address': '654 Đường JKL, Quận 5, TP.HCM',
                'position': 'Thực tập sinh',
                'department': 'Vận hành',
                'hire_date': date(2024, 1, 1),
                'salary': 8000000,
                'allowance': 500000
            }
        ]

        for emp_data in employees_data:
            employee = Employee(**emp_data)
            db.session.add(employee)
        print("✓ Đã tạo 5 nhân viên mẫu")

        db.session.commit()

        # Tạo attendance records cho tháng hiện tại (theo múi giờ +07)
        current_time = datetime.utcnow().replace(tzinfo=None)  # Lấy giờ UTC
        vietnam_offset = timedelta(hours=7)  # Múi giờ Việt Nam +07
        vietnam_time = current_time + vietnam_offset
        current_month = vietnam_time.month
        current_year = vietnam_time.year
        
        for employee in Employee.query.all():
            for day in range(1, 21):
                if day <= 20:  # Chỉ tạo cho 20 ngày đầu tháng
                    attendance_date = date(current_year, current_month, day)
                    if attendance_date.weekday() < 5:  # Skip weekends
                        check_in_time = datetime.combine(attendance_date, datetime.min.time().replace(hour=8, minute=random.randint(0, 30)))
                        check_out_time = datetime.combine(attendance_date, datetime.min.time().replace(hour=17, minute=random.randint(0, 30)))
                        
                        total_hours = (check_out_time - check_in_time).total_seconds() / 3600
                        overtime_hours = max(0, total_hours - 8)
                        
                        attendance = Attendance(
                            employee_id=employee.id,
                            date=attendance_date,
                            check_in=check_in_time,
                            check_out=check_out_time,
                            total_hours=round(total_hours, 2),
                            overtime_hours=round(overtime_hours, 2),
                            status='present'
                        )
                        db.session.add(attendance)
        
        print("✓ Đã tạo dữ liệu chấm công cho tháng hiện tại")

        db.session.commit()
        print("✓ Hoàn thành khởi tạo dữ liệu mẫu!")

def main():
    """Hàm chính chạy trên Railway"""
    print("🚀 Bắt đầu khởi tạo hệ thống quản lý nhân sự trên Railway...")
    
    try:
        # Cấu hình database URL từ Railway
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            "connect_args": {"ssl": {"fake_flag_to_enable_tls": True}}  # SSL cho Railway
        }
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        init_database()
        create_sample_data()
        print("\n🎉 Khởi tạo thành công!")
        print("\n📋 Thông tin đăng nhập:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n🔗 Truy cập ứng dụng tại URL do Railway cung cấp (xem trong tab Domains)")

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        with app.app_context():
            db.session.rollback()

if __name__ == '__main__':
    main()