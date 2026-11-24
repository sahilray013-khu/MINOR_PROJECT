# Accreditation & Institutional Data Management System

A full-stack React and Django REST application for institutional data, accreditation frameworks, evidence management, submissions, verification, approvals, reports, notifications, and audit history.

## Technology

- React 19, React Router, Axios, Recharts, Lucide
- Django 5, Django REST Framework, SimpleJWT
- SQLite for zero-setup development; PostgreSQL for the requested production database
- OpenPyXL and ReportLab for Excel/PDF reports

## Backend setup

```powershell
cd C:\MinorProject\backend
py -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py populate_dashboard_demo_data
python manage.py runserver
```

Backend: `http://127.0.0.1:8000`

`populate_dashboard_demo_data` safely adds sample records for Dev Bhoomi University until each dashboard data type has at least 15 records. It preserves existing data and can be rerun without intentionally duplicating its named demo entries. Sample departments, programmes, placements, submissions, and evidence are illustrative.

Demo password for all seeded users: `Password@123`

- `admin` - Super Admin
- `institution` - Institutional Admin
- `coordinator` - Accreditation Coordinator
- `department` - Department Admin
- `faculty` - Faculty/Staff
- `reviewer` - Reviewer/Verifier
- `viewer` - Management Viewer

## Student accounts

Students can register or sign in from **Student login or registration** on the login page, or directly at `/student-register` and `/student-login`. Registration requires the university, department, programme, and academic year. The student account and student record are created together, and the record is linked to the selected university through its department. Student accounts only see their own student profile; institutional records remain available in the staff dashboard.

The demo catalogue includes departments for BBA, MBA, BCA, hotel management, pharmacy, and nursing, with multiple programme/stream choices where applicable. These are sample choices and should be checked against the university's official catalogue before real enrollment.

Student login and student registration are available as tabs on the same student access page (`/student-login` or `/student-register`).

University administrators can bulk-load student records from **Students → Import Excel**. Download the workbook template first; fill one student per row using the university's department and programme codes and an existing academic-year name. The import supports `.xlsx` files up to 10 MB and 5,000 rows. It validates the complete workbook before saving, so a workbook with errors imports no rows. Bulk import creates student records, not student login accounts. Super admins select a university; institutional admins can import only into the university associated with their account.

## Bulk Excel imports

Super admins and institutional admins can download templates and import records from Institutions, Academic Years, Facilities, Departments, Programmes, Courses, Faculty, Students, Research, Publications, Placements, Accreditation Frameworks, Criteria, Parameters, Evidence, and Submissions. Each non-student section has a matching `Data` sheet and reference sheets for foreign-key IDs. Imports accept `.xlsx` files up to 10 MB and 5,000 rows, validate the full workbook, and save all rows or none. Institutional admins are restricted to their linked university; super admins can import across institutions. Institution imports are super-admin-only.

Evidence imports require one uploaded document for each `file_name` in the workbook. Documents must use an allowed extension, be at most 10 MB each, and total no more than 50 MB. Submissions are always imported as drafts and must use the existing submit/review/approve workflow. User accounts, notifications, audit history, and workflow review events are not bulk-imported. Optional document fields on faculty, research, and publication records are not included in the Excel template and must be attached separately.

After updating the backend, apply the new student-account migration:

```powershell
cd C:\MinorProject\backend
python manage.py migrate
```

## Frontend setup

```powershell
$env:Path="C:\Program Files\nodejs;$env:Path"
cd C:\MinorProject\frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## PostgreSQL setup

1. Install/start PostgreSQL 17.
2. Create a database:

```sql
CREATE DATABASE accreditation_db;
```

3. Copy `backend/.env.example` to `backend/.env` and set the PostgreSQL values.
4. PowerShell environment variables can also be set before running Django.
5. Run migrations and seed data.

The settings use SQLite unless `POSTGRES_DB` is set.

### Docker PostgreSQL and backend

```powershell
docker compose up -d --build postgres backend frontend
```

The backend container runs migrations and seed data automatically. Default PostgreSQL port:
`5432`; database: `accreditation_db`; user: `postgres`; password: `change-me`.

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Health check: `http://localhost:8000/api/health/`

Stop containers:

```powershell
docker compose down
```

## API documentation

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI JSON: `http://127.0.0.1:8000/api/schema/`

JWT login:

- `POST /api/auth/login/` with `{"username":"admin","password":"Password@123"}`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`

Main endpoints:

- `/api/departments/`, `/api/programmes/`, `/api/courses/`
- `/api/faculty/`, `/api/students/`, `/api/placements/`
- `/api/research-projects/`, `/api/publications/`
- `/api/frameworks/`, `/api/criteria/`, `/api/parameters/`
- `/api/evidence/`, `/api/submissions/`, `/api/notifications/`, `/api/audit/`
- `/api/dashboard/`
- `/api/report-download/?type=faculty&format=xlsx`
- `/api/auth/profile/` for profile updates
- `/api/auth/change-password/` for password changes

Submission actions:

- `POST /api/submissions/{id}/submit/`
- `POST /api/submissions/{id}/review/` with `decision` and `comments`
- `POST /api/submissions/{id}/approve/`

## Testing

Use the project verification script:

```powershell
cd C:\MinorProject
.\verify-project.ps1
```

Start all local services:

```powershell
cd C:\MinorProject
.\start-project.ps1
```

```powershell
cd C:\MinorProject\backend
python manage.py test core
```

Frontend production build:

```powershell
cd C:\MinorProject\frontend
npm run build
```

## Security and deployment

- Never commit real secrets or upload credentials.
- Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, and exact production hosts and CORS origins.
- Use HTTPS, PostgreSQL TLS where supported, restricted media storage, regular backups, and log retention.
- Evidence uploads are limited to 10 MB and permitted document extensions.
- Audit logs are read-only to ordinary API users and restricted to administrative roles.
