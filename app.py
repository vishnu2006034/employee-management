from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_login import UserMixin
from flask_wtf import FlaskForm
from apscheduler.schedulers.background import BackgroundScheduler
import cv2
import numpy as np
import base64
import os
import matplotlib.pyplot as plt
from PIL import Image
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Create a file handler
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.ERROR)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
today=date.today().strftime('%Y-%m-%d')
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
app.config['SECRET_KEY'] = 'haihitler'
app.config['UPLOAD_FOLDER'] = 'static/profilepic/'
login = LoginManager(app)
login.login_view = 'emplogin'

db = SQLAlchemy(app)

# to create a manager login password
class Man(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(150))

# to create a employee details
class Emp(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    contact = db.Column(db.Integer, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)
    department = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    picture = db.Column(db.String, default='default.img')
    attendance = db.Column(db.Integer)
    points = db.Column(db.Integer, default=100, nullable=False)
    tasks = db.relationship('Task', backref='employee', lazy=True)
    #shifts = db.relationship('Shift',backref='employee',lazy=True)
# to create a task for employee
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    duetime = db.Column(db.DateTime)
    status = db.Column(db.Text, nullable=False, default="incomplete")
    user_id = db.Column(db.Integer, db.ForeignKey('emp.id'), nullable=False)

# to put attendence for employee
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('emp.id'), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False, default="absent")

# to make today working day
class Workingday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(150))

# to create shift variable
class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

# to assign shift for employee
class Shiftassign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.Integer, db.ForeignKey('emp.id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id'), nullable=False)
    date = db.Column(db.Date, nullable=True)
shift1=db.relationship('Shift',backref=db.backref('Shiftassign',lazy=True))

# for decode the image
def decode(base64_string):
    try:
        base64_data = base64_string.split(',')[1]
        img_data = base64.b64decode(base64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(e)
        return None

# to get the user id from the emp.db with session
@login.user_loader
def load_user(user_id):
    try:
        return Emp.query.get(int(user_id))
    except Exception as e:
        logger.error(e)
        return None

# it is the route for first page
@app.route('/')
def index():
    try:
        return render_template('firstpage.html ')
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for admin login page
@app.route('/manpage', methods=['GET', 'POST'])
def manpage():
    try:
        if request.method == "POST":
            code = "12345"
            hpassword = Man(password=code)  # assigns code to the password
            db.session.add(hpassword)  # stores the hpassword in session and saves in db
            db.session.commit()
            password = request.form.get('password')  # it get the password from user
            passes = Man.query.filter_by(password=code).first()  # it takes the first value in man.db which is the first code stored
            if password == passes.password:  # checks the user entered with the db password
                return redirect('manpro')  # guides to the admin page
            else:
                return redirect(url_for('index'))  # return to the first page
        return render_template('adminlogin.html')  # html file for the admin
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500
    
@app.route('/manpro', methods=["GET", "POST"])
def manpro():
    try:
        if request.method == "POST":
            existingday = Workingday.query.filter_by(date=today).first()  # indicates the working day added already
            if existingday:  # if the working day is already added
                flash("already working day added", "info")
                return redirect('/manpro')  # return to the admin profile
            newday = Workingday(date=today)  # to add new working day
            db.session.add(newday)
            db.session.commit()
            flash("working day successfully added", 'info')
            return redirect('manpro')
        imgs = []  # creating a new imgs list to store the image
        imagefile1 = url_for('static', filename='profilepic/admin pic.png')  # picture for admin profile
        # showing employee details with their photo
        employees = Emp.query.all()
        for emp in employees:
            imagefile = url_for('static', filename='profilepic/' + emp.picture)  # employee photo
            imgs.append(imagefile)
        return render_template('adminpage.html', emps=employees, imgs=imgs, zip=zip, img1=imagefile1)  # return emp details photo and admin  photo
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for employee registration
@app.route('/empreg', methods=["GET", "POST"])
def empreg():
    try:
        if current_user.is_authenticated:  # if the employee password is correct open the employee profile
            return redirect(url_for('emppro'))
        if request.method == "POST":  # to get information for employee
            name = request.form.get('name')
            email = request.form.get('email')
            department = request.form.get('dep')
            contact = request.form.get('contact')
            age = request.form.get('age')
            gender = request.form.get('gender')
            password = request.form.get('password')
            picture = request.files['picture']
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], picture.filename)  # for uploading the file
            picture.save(filepath)
            newemp = Emp(name=name, email=email, department=department, contact=contact, age=age, gender=gender, password=password, picture=picture.filename)
            db.session.add(newemp)
            db.session.commit()
            flash("account is successfully created", "success")
            return redirect(url_for('emplogin')) # after the registraion returns to login page
        else:
            flash("check for the account already exists")
        return render_template("empreg.html")  # it is the registration html
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for employee login
@app.route('/emplogin', methods=["GET", "POST"])
def emplogin():
    try:
        if current_user.is_authenticated:  # checks the email and password
            return redirect(url_for('emppro'))
        if request.method == "POST":
            email = request.form.get('email')
            password = request.form.get('password')
            emp = Emp.query.filter_by(email=email).first()
            if emp and emp.password == password:  # if the email and pass match show the profile
                login_user(emp)
                return redirect(url_for('emppro'))
            else:
                flash("login details is wrong", "error")
        return render_template("front end.html")  # empsigin
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for employee profile
@app.route("/emppro")
@login_required
def emppro ():
    try:
        imagefile = url_for('static', filename='profilepic/' + current_user.picture)
        assigned_shifts = Shiftassign.query.filter_by(emp_id=current_user.id).all()  # shows the employee photo
        return render_template("employee profile.html", img=imagefile,assigned_shifts=assigned_shifts)  # it is the employee detail html
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for task assigning
@app.route("/assign")
@login_required
def assign():
    try:
        task = Task.query.filter_by(user_id=current_user.id).all()  # takes the task from db
        return render_template("task.html", assigns=task)  # it is the task html
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for task submitting
@app.route("/submit/<int:taskid>", methods=["POST"])  # submit the task
@login_required  # login is mandatory
def submit(taskid):
    try:
        submit = Task.query.get(taskid)  # specifics the task with their id
        if datetime.now() > submit.duetime:  # if the task is incomplete
            current_user.points -= 10  # mark will be reduced
            db.session.commit
        else:  # if finished
            current_user.points += 10  # he regain the mark
        db.session.delete(submit)  # deletes the task after finished
        db.session.commit()
        return redirect(url_for('assign'))  # returns submission to the assign
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for attendence
@app.route('/attend', methods=["GET", "POST"])
@login_required
def attend():
    try:
        if request.method == "POST":
            userid = request.json.get('username')  # client send json with object
            if userid == "hailhitler":  # qrcode with hailhitler name
                emp = Emp.query.filter_by(id=current_user.id).first()  # takes the employee from db
                attendance = Attendance.query.filter_by(user_id=emp.id, date=today, status="present").first()  # indicates the attendence marked
                if not attendance:  # if not marked
                    newattend = Attendance(user_id=emp.id, date=today, status="present")  # new attendence will be marked
                    db.session.add(newattend)  # adding attendence
                    db.session.commit()
                    flash('Attendance Entered')
                    return jsonify({'status': 'success', 'message': f'Attendance marked'}), 200
            else:
                flash("attendence is already entered")
                return redirect('emppro')  # returns to the emp profile
        return render_template("attendance.html")  # it is the attendence html template
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for admin to see the employees details
@app.route("/manpage/<int:emp_id>", methods=["GET", "POST"])  # clicks the employee id
def emp(emp_id):
    try:
        if request.method == "POST":
            emp = Emp.query.get_or_404(emp_id)  # gets the employee id
            content = request.form.get("content")  # retreive the content
            duetime = request.form.get("duetime")  # also the due time
            print(duetime)
            duetime = duetime.replace("T", " ")  # replace the t with the space for html indication
            duetime = duetime + ":00.100000"
            duetime = datetime.strptime(duetime, "%Y-%m-%d %H:%M:%S.%f")  # converts the time to date format
            post = Task(content=content, employee=emp, duetime=duetime)  # creating a new task for employee
            db.session.add(post)  # adding the task
            db.session.commit()
        emp = Emp.query.get_or_404(emp_id)
        imagefile = url_for('static', filename='profilepic/' + emp.picture)  # picture for employee
        return render_template("employee details.html", emp=emp, img=imagefile)  # html file for emp details
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# matplotlib for plotting the attendee details
def matplot():
    try:
        employees = Emp.query.all()  # list of employees
        total = Workingday.query.count()  # total number of present
        name = [emp.name for emp in employees] 
        points = [emp.points for emp in employees]
        for emp in employees:  # for loop for emp
            attend = Attendance.query.filter_by(user_id=emp.id).count()  # it stores the employee presented in attend
            emp.attendance = (attend / total) * 100  # calculating the attendence percentage
            db.session.commit()
        attendance = [emp.attendance for emp in employees]  # stores the attendence percentage for each employee
        plt.bar(name, attendance, color="blue") 
        plt.xlabel('Employee Names')
        plt.ylabel('Points')
        plt.title('Employee Attendence')
        plt.savefig("static/attend.png")
        plt.bar(name, points, color="red")  # bar graph for each employee attendance
        plt.xlabel('Employee Names')
        plt.ylabel('Points')
        plt.title('Employee task points')
        plt.savefig("static/point.png")  # save the graph
        plt.close()  # save the graph
    except Exception as e:
        logger.error(e)


# route for logging out
@app.route("/logout")
def logout():
    try:
        logout_user()  # log out user
        return redirect(url_for('emplogin'))  # returns to the login page
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

@app.route("/shiftshow")
@login_required
def shiftshow():
    #try:
    # sshifts = Shiftassign.query.filter_by(emp_id=current_user.id).all()
    # shift_ids=[s.shift_id for s in sshifts]
    # shift2=Shift.query.filter(Shift.id.in_(shift_ids)).all()
    shift2= db.session.query(Shiftassign,Shift).join(Shift,Shiftassign.shift_id==Shift.id).filter(Shiftassign.emp_id == current_user.id).all()
    return render_template("shiftshow.html", shifts=shift2)
    #except Exception as e:
        #logger.error(e)
        #return render_template('500.html'), 500
# route for shift assignin     m g
@app.route("/shift", methods=["GET", "POST"])
def shift():
    try:
        if request.method == "POST":
            emps = request.form.getlist('employees')  # get the list of employees
            shift_id = request.form.get('shift')  # gets the id from shift db
            shift_date = request.form.get('shiftdate')  # gets the date from the shift db
            for emp in emps:
                assignment = Shiftassign(emp_id=emp, shift_id=shift_id, date=datetime.strptime(shift_date, "%Y-%m-%d"))  # assigns the shift for the emp with date
                db.session.add(assignment)  # add the assignment to the session
                db.session.commit()
            return redirect(url_for('manpro'))  # returns to the admin profile
        emps = Emp.query.all()  # emps is employee
        shifts = Shift.query.all()  # shifts is the details of shift
        return render_template("shift assign.html", emps=emps, shifts=shifts)
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for admin dashboard
@app.route("/dash")
def dashboard():
    try:
        task=Task.query.count()
        attend = Attendance.query.filter_by(date=today).count()  # shows the number of present
        emp1 = Emp.query.count() 
        matplot()
        imagefile = url_for('static', filename='attend.png')
        imagefile1 = url_for('static', filename='point.png')
        return render_template("employee dashboard-3.html",emp=emp1,empp=attend,task=task ,img=imagefile,img1=imagefile1) 
        
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

# route for admin to see the today shifts
@app.route("/toshift")
def toshift():
    try:
        todayshift = Shiftassign.query.filter_by(date=today).all()  # takes today shift from db
        mornames = []
        evenames = []
        nitnames = []
        for shift in todayshift:  # loop for each employee shift
            shit = shift.shift_id  # it is shift id
            empi = shift.emp_id  # it is the emp id
            if shit == 1:  # IF EMP is morning shift
                emp = Emp.query.filter_by(id=empi).first()
                mornames.append(emp.name)  # stores emp to mornames list
            if shit == 2:  # IF EMP is evening shift
                emp = Emp.query.filter_by(id=empi).first()
                evenames.append(emp.name)  # stores emp to evenames list
            if shit == 3:  # IF EMP is night shift
                emp = Emp.query.filter_by(id=empi).first()
                nitnames.append(emp.name)  # stores emp to nitnames list
        mornames1 = list(dict.fromkeys(mornames))
        evenames1 = list(dict.fromkeys(evenames))
        nitnames1 = list(dict.fromkeys(nitnames))
        return render_template('shifts.html', mornames=mornames1, evenames=evenames1, nitnames=nitnames1)
    except Exception as e:
        logger.error(e)
        return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(e)
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(e)
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app .app_context():
        db.create_all()
    app.run(debug=True)

