"""
Digital Library Web App
========================
Flask-based web application to manage a personal book library.
Features include:
- Adding and managing authors
- Adding and managing books
- Searching and sorting books
- Deleting books
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'  # SQLite database file
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Define Author model
class Author(db.Model):
    """Model representing a book author."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date)
    books = db.relationship('Book', backref='author', lazy=True)

# Define Book model
class Book(db.Model):
    """Model representing a book."""
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

@app.route('/')
def home():
    """Home page: display books, optionally filtered and sorted."""
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', '')

    books_query = Book.query

    if search_query:
        books_query = books_query.filter(Book.title.ilike(f"%{search_query}%"))

    if sort_by == 'title':
        books_query = books_query.order_by(Book.title.asc())
    elif sort_by == 'author':
        books_query = books_query.join(Author).order_by(Author.name.asc())

    books = books_query.all()
    return render_template('home.html', books=books)

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """Form to add a new author."""
    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birth_date']
        date_of_death = request.form['date_of_death']

        birth_date = datetime.strptime(birth_date, '%Y-%m-%d') if birth_date else None
        date_of_death = datetime.strptime(date_of_death, '%Y-%m-%d') if date_of_death else None

        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
        db.session.add(new_author)
        db.session.commit()

        flash('Author added successfully!', 'success')
        return redirect(url_for('add_author'))

    return render_template('add_author.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """Form to add a new book."""
    authors = Author.query.all()

    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        new_book = Book(
            isbn=isbn,
            title=title,
            publication_year=int(publication_year),
            author_id=int(author_id)
        )
        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))

    return render_template('add_book.html', authors=authors)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """Delete a book by ID."""
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{book.title}" was deleted.', 'success')
    return redirect(url_for('home'))

# Create all tables if they don't exist
with app.app_context():
    db.create_all()

# Start the app (Codio port fix)
if __name__ == '__main__':
    app.run(debug=True, port=5002, host='0.0.0.0')