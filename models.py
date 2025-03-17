from app import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    employees = db.Column(db.String(200), nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)