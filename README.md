# Django MongoDB MQL Panel

Configure the MongoDB Query Language (MQL) panel in Django MongoDB Extensions to use with the Django Debug Toolbar, built with a World Cup 2026 analytics app.

## Prerequisites

- Python 3.13+
- MongoDB Atlas cluster (or local MongoDB instance)
- Django 6.0+

## Setup

1. Clone the repo and create a virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/django-mongodb-mql-panel.git
cd django-mongodb-mql-panel
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install django-mongodb-backend django-mongodb-extensions
```

3. Set your MongoDB connection string:

```bash
export MONGODB_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/worldcup?retryWrites=true&w=majority"
```

4. Run migrations and load data:

```bash
python manage.py migrate
python manage.py load_matches
```

5. Start the server:

```bash
python manage.py runserver
```

6. Visit [http://localhost:8000](http://localhost:8000) and use the Django Debug Toolbar's MQL panel to inspect queries.
