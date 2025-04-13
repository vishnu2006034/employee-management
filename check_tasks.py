from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False, default="incomplete")
    user_id = db.Column(db.Integer, db.ForeignKey('emp.id'), nullable=False)

with app.app_context():
    tasks = Task.query.all()
    for task in tasks:
        print(f'Task ID: {task.id}, Content: {task.content}, Status: {task.status}')
