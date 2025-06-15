from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date)
    books = db.relationship('Book', backref='author', lazy=True)

    def __str__(self):
        birth = self.birth_date.strftime('%Y-%m-%d') if self.birth_date else "Unbekannt"
        death = self.date_of_death.strftime('%Y-%m-%d') if self.date_of_death else "Lebt"
        return f'<Author: {self.name}, Geboren: {birth}, Gestorben: {death}>'

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(150), nullable=False)
    publication_year = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)

    def __str__(self):
        return f'<Book: {self.title}, ISBN: {self.isbn or "N/A"}, Jahr: {self.publication_year or "Unbekannt"}>'
