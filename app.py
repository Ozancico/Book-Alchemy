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
from data.models import db, Author, Book
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'  # SQLite database file
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

def normalize_isbn(isbn):
    """Entfernt alle Bindestriche und Leerzeichen aus der ISBN."""
    if not isbn:
        return None
    return ''.join(c for c in isbn if c.isdigit() or c.lower() == 'x')

def format_isbn(isbn):
    """Formatiert eine normalisierte ISBN mit Bindestrichen."""
    if not isbn:
        return ""
    if len(isbn) == 13:  # ISBN-13
        return f"{isbn[0:3]}-{isbn[3]}-{isbn[4:7]}-{isbn[7:12]}-{isbn[12]}"
    elif len(isbn) == 10:  # ISBN-10
        return f"{isbn[0]}-{isbn[1:4]}-{isbn[4:9]}-{isbn[9]}"
    return isbn

def validate_date(date_str):
    """Validiert und konvertiert verschiedene Datumsformate in datetime.
    Unterstützt Formate wie:
    - YYYY-MM-DD
    - DD.MM.YYYY
    - YYYY
    """
    if not date_str or date_str.strip() == "":
        return None

    date_str = date_str.strip()

    # Versuche verschiedene Datumsformate
    formats = [
        "%Y-%m-%d",    # 1989-12-31
        "%d.%m.%Y",    # 31.12.1989
        "%Y"           # 1989
    ]

    for fmt in formats:
        try:
            if len(date_str) == 4 and fmt == "%Y":  # Nur Jahreszahl
                return datetime(int(date_str), 1, 1)
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Ungültiges Datumsformat: {date_str}. Bitte verwenden Sie YYYY-MM-DD, DD.MM.YYYY oder YYYY")

def validate_isbn(isbn):
    """Validiert eine ISBN-Nummer."""
    if not isbn:
        return None

    # Entferne alle nicht-alphanumerischen Zeichen
    cleaned_isbn = normalize_isbn(isbn)

    # Prüfe die Länge
    if len(cleaned_isbn) not in [10, 13]:
        raise ValueError(f'ISBN muss 10 oder 13 Stellen haben, hat aber {len(cleaned_isbn)} Stellen')

    return cleaned_isbn

def validate_year(year):
    """Validiert ein Erscheinungsjahr."""
    try:
        year = int(year)
        current_year = datetime.now().year

        # Erste Bücher wurden ca. ab Jahr 1450 gedruckt (Gutenberg-Bibel)
        if year < 1450 or year > current_year + 1:  # +1 für Bücher die fürs nächste Jahr angekündigt sind
            raise ValueError(f'Das Jahr muss zwischen 1450 und {current_year + 1} liegen')

        return year
    except ValueError as e:
        if str(e).startswith('Das Jahr muss'):
            raise
        raise ValueError('Das Jahr muss eine gültige Zahl sein')

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
        name = request.form['name'].strip()
        birth_date_str = request.form['birth_date']
        death_date_str = request.form['date_of_death']

        if not name:
            flash('Der Name des Autors darf nicht leer sein.', 'error')
            return render_template('add_author.html')

        try:
            birth_date = validate_date(birth_date_str) if birth_date_str else None
            date_of_death = validate_date(death_date_str) if death_date_str else None

            # Prüfe, ob das Sterbedatum nach dem Geburtsdatum liegt
            if birth_date and date_of_death and date_of_death < birth_date:
                flash('Das Sterbedatum kann nicht vor dem Geburtsdatum liegen.', 'error')
                return render_template('add_author.html')

            # Prüfe, ob die Daten in der Zukunft liegen
            today = datetime.now()
            if birth_date and birth_date > today:
                flash('Das Geburtsdatum kann nicht in der Zukunft liegen.', 'error')
                return render_template('add_author.html')
            if date_of_death and date_of_death > today:
                flash('Das Sterbedatum kann nicht in der Zukunft liegen.', 'error')
                return render_template('add_author.html')

            new_author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death
            )
            db.session.add(new_author)
            db.session.commit()
            flash('Autor wurde erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('add_author'))

        except ValueError as e:
            flash(str(e), 'error')
            return render_template('add_author.html')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hinzufügen des Autors: {str(e)}', 'error')
            return render_template('add_author.html')

    return render_template('add_author.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """Form to add a new book."""
    authors = Author.query.all()

    if request.method == 'POST':
        try:
            # Validiere ISBN
            isbn = validate_isbn(request.form['isbn'])

            # Validiere Jahr
            publication_year = validate_year(request.form['publication_year'])

            title = request.form['title'].strip()
            if not title:
                raise ValueError('Der Titel darf nicht leer sein')

            author_id = request.form['author_id']

            # Prüfe, ob die ISBN bereits existiert (nach Normalisierung)
            existing_book = Book.query.filter_by(isbn=isbn).first()
            if existing_book:
                flash(f'Ein Buch mit der ISBN {format_isbn(isbn)} existiert bereits.', 'error')
                return render_template('add_book.html', authors=authors)

            new_book = Book(
                isbn=isbn,
                title=title,
                publication_year=publication_year,
                author_id=int(author_id)
            )

            db.session.add(new_book)
            db.session.commit()
            flash('Buch wurde erfolgreich hinzugefügt!', 'success')
            return redirect(url_for('add_book'))

        except ValueError as e:
            flash(str(e), 'error')
            return render_template('add_book.html', authors=authors)
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hinzufügen des Buches: {str(e)}', 'error')
            return render_template('add_book.html', authors=authors)

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
    app.run(debug=True, port=5003, host='0.0.0.0')