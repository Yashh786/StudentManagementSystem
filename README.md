# Atlas Student Records

Atlas Student Records is a local-first student management system with a polished browser workspace and a matching Python command-line interface. It keeps the workflow simple: enter student details, review performance, and export the records when needed.

## Features

- Create, edit, view, and delete student records
- Validate IDs, ages, courses, and marks from 0 to 100
- Search by student name, course, or ID
- Sort by name, average, or ID
- Filter by grade and see class-level statistics
- View detailed student profiles in a modal dialog
- Import and export compatible JSON files
- Persist browser changes in localStorage
- Use the same data model from the Python CLI

## Run It

### Browser workspace

Open `index.html` directly in a browser. No build step or server is required.

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
	"01": {
		"name": "Yash",
		"age": 20,
		"course": "Computer Science",
		"marks": {
			"Math": 90,
			"Science": 78,
			"English": 88
		}
	}
}
```

The browser stores its working copy in localStorage. Use **Export records** to create a JSON file that can be imported by either interface.