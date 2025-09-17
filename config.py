import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '0ach-7L4clBYZ_MSXXUI2mvcEJTCFmWPr0f-cFrv2Ek')
   
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:77866@localhost/hr_management"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1')
