# Atlas Student Records

Atlas Student Records is an authenticated student management system with a polished browser workspace, database-backed records, and a matching Python command-line interface.

## Features

- Create, edit, view, and delete student records
- Validate IDs, ages, courses, and marks from 0 to 100
- Search by student name, course, or ID
- Sort by name, average, or ID
- Filter by grade and see class-level statistics
- Track attendance and identify students below the 75% support threshold
- Filter the directory by healthy or at-risk attendance
- View detailed student profiles in a modal dialog
- Import and export compatible JSON files
- Secure account registration and login with hashed passwords
- Per-user record ownership with CSRF-protected API mutations
- SQLite development database with PostgreSQL-compatible production configuration
- Offline app shell through a service worker without caching private API responses

## Run It

### Development setup

Requires Python 3.13 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m flask --app app db upgrade
python -m flask --app app run
```

Open `http://127.0.0.1:5000` and create an account. Run tests with:

```powershell
python -m pytest -q
```

### Deploy the browser app

The application now requires the Flask server for authentication and database access. Deploy it with a production WSGI server, not Flask's development server:

```powershell
$env:FLASK_ENV="production"
$env:SECRET_KEY="use-a-long-random-secret"
$env:DATABASE_URL="postgresql+psycopg://user:password@host:5432/atlas"
$env:COOKIE_SECURE="1"
python -m flask --app app db upgrade
waitress-serve --call app:create_app
```

Set the same values in the hosting provider's environment configuration. HTTPS is required when `COOKIE_SECURE=1`. SQLite is suitable for development or a single small deployment; PostgreSQL is recommended for real multi-user use.

The browser still has an offline app shell, but private API responses are deliberately excluded from the service-worker cache.

For a static-only preview of the visual shell:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`. Authentication and database features require the Flask server.

### Python CLI

Requires Python 3.9 or newer.

```powershell
python StudentManagement.py
```

The CLI reads from and saves to `students_data.json` in the project directory.

## Data Format

Records use a dictionary keyed by student ID:

```json
{
	"100": {
		"name": "Demo Student",
		"age": 18,
		"course": "Computer Science",
		"attendance": 92,
		"marks": {
			"Math": 85,
			"Science": 82,
			"English": 88
		}
	}
}
```

Use **Export records** to create a JSON backup. Web records are stored in the configured database and are scoped to the signed-in account.