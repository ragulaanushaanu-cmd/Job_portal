# Job Portal

A full-stack job portal built with **FastAPI, React, MySQL, SQLAlchemy, JWT authentication, role-based access control, resume parsing, and ATS resume-to-job matching**.

The project is designed as a production-oriented portfolio application demonstrating backend architecture, database design, authentication and authorization, API development, automated testing, deployment, and practical ATS logic.

---

## Overview

The Job Portal connects candidates and employers through a single full-stack platform.

### Candidate Workflow

Candidates can:

- Register and authenticate securely
- Manage their candidate profile
- Browse and search jobs
- Filter and sort jobs
- Save jobs for later
- Upload and manage resumes
- Set a primary resume
- Parse resumes into structured data
- Apply for jobs
- Track application status and history
- Analyze resumes against jobs using the ATS system

### Employer Workflow

Employers can:

- Authenticate through the platform
- Create and manage companies
- Create, edit, and delete jobs
- View applications submitted to their jobs
- Update application statuses
- View application history
- Manage company and job information
- View employer dashboard statistics

---

## Live Application

### Frontend

https://acceptable-beauty-production-29df.up.railway.app

### Backend API

https://jobportal-production-4e27.up.railway.app

### Swagger Documentation

https://jobportal-production-4e27.up.railway.app/docs

### Health Check

https://jobportal-production-4e27.up.railway.app/health

---

# Key Features

## Authentication & Authorization

- JWT-based authentication
- Password hashing with bcrypt
- Candidate, Employer, and Admin roles
- Role-based access control
- Protected FastAPI endpoints
- Ownership validation for user-specific resources
- Environment-based configuration

## Job Management

- Job creation and management
- Job search
- Location filtering
- Salary information
- Employment type
- Experience level
- Work mode
- Pagination
- Sorting
- Employer ownership validation

## Resume Management

- PDF and DOCX upload
- File type and signature validation
- File size validation
- Secure stored filenames
- Resume listing
- Resume download
- Primary resume selection
- Resume deletion
- Resume parsing
- Parser version tracking
- Structured resume data
- Persistent resume storage using Railway Volume

## Applications

- Candidate job applications
- Resume selection during application
- Duplicate application protection
- Application status tracking
- Application status history
- Candidate access control
- Employer access control

## Candidate Profile

- Headline
- Bio
- Phone
- Location
- Experience
- Education
- Skills
- LinkedIn
- GitHub
- Portfolio

## Saved Jobs

- Save jobs
- List saved jobs
- Remove saved jobs
- Duplicate-save protection

## Dashboards

### Candidate Dashboard

Includes:

- Resume count
- Application count
- Saved job count
- Primary resume
- Application status breakdown
- Recent applications

### Employer Dashboard

Includes:

- Owned companies
- Total jobs
- Total applications
- Shortlisted applications
- Selected applications
- Application status breakdown
- Recent applications

---

# ATS Resume Matching System

One of the main features of this project is an ATS-style resume analysis system.

The system compares structured resume information against a target job and produces a weighted compatibility score.

## ATS Pipeline

```text
Resume Upload
      ↓
Resume Parsing
      ↓
Structured Resume Data
      ↓
Skill Canonicalization
      ↓
ATS Keyword Extraction
      ↓
Education Hierarchy Matching
      ↓
Experience Relevance
      ↓
Project Relevance
      ↓
Weighted ATS Score
      ↓
Matched / Missing Skills & Keywords
      ↓
Recommendations

ATS Scoring
Component	Weight
Skills	40%
Keywords	25%
Experience	20%
Education	15%

The ATS result includes:

Overall ATS score
Skill score
Keyword score
Experience score
Education score
Matched skills
Missing skills
Matched keywords
Missing keywords
Recommendations
ATS Engineering Details

The ATS implementation includes:

Skill canonicalization
Skill alias handling
Phrase-aware matching
Singular/plural normalization
Meaningful keyword filtering
Generic keyword rejection
Technical skill exclusion from ordinary keyword extraction
Education hierarchy matching
Education field/specialization matching
Required experience extraction
Project relevance based on ATS keywords
Canonical keyword deduplication
Recommendation generation from detected gaps
Parser-version readiness validation
Resume ownership validation
Unique resume/job ATS analysis handling
Architecture

The application follows a layered backend architecture:

React Frontend
      ↓
FastAPI Routers
      ↓
Service Layer
      ↓
SQLAlchemy ORM
      ↓
MySQL Database

Cross-cutting concerns include:

Authentication
Authorization / RBAC
Validation
Error Handling
Database Transactions
File Handling
Pagination
Logging

The backend separates HTTP/API responsibilities from business logic through routers and service modules.

Technology Stack
Backend
Python
FastAPI
Pydantic
SQLAlchemy
MySQL
PyMySQL
Alembic
python-jose
Passlib / bcrypt
python-dotenv
Uvicorn
Frontend
React
Vite
Axios
JavaScript
React Router
Testing
pytest
FastAPI TestClient
SQLite-based isolated test database
GitHub Actions
Deployment
Railway
Railway MySQL
Railway Volume
Docker
GitHub Actions CI
Project Structure
Job_portal/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   ├── candidate/
│   │   │   └── employer/
│   │   ├── routes/
│   │   └── utils/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── routers/
│   ├── applications.py
│   ├── ats_router.py
│   ├── auth.py
│   ├── companies.py
│   ├── dashboard_router.py
│   ├── employer_company_router.py
│   ├── employer_dashboard_router.py
│   ├── employer_jobs_router.py
│   ├── jobs.py
│   ├── profile_router.py
│   ├── resumes.py
│   ├── saved_job_router.py
│   └── users.py
│
├── services/
│   ├── application_service.py
│   ├── ats_service.py
│   ├── company_service.py
│   ├── dashboard_service.py
│   ├── employer_company_service.py
│   ├── employer_dashboard_service.py
│   ├── employer_job_service.py
│   ├── job_service.py
│   ├── profile_service.py
│   ├── resume_parser_service.py
│   ├── resume_service.py
│   ├── saved_job_service.py
│   └── user_service.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_application.py
│   ├── test_ats.py
│   ├── test_ats_service.py
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_dashboard.py
│   ├── test_employer_dashboard.py
│   ├── test_health.py
│   ├── test_jobs.py
│   ├── test_profile.py
│   ├── test_resume.py
│   └── test_saved_job.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── alembic.ini
├── auth.py
├── database.py
├── dependencies.py
├── exceptions.py
├── main.py
├── models.py
├── requirements.txt
└── schemas.py
Database Design

The application uses MySQL with SQLAlchemy ORM and Alembic.

Major Entities
User
CandidateProfile
Company
Job
SavedJob
Application
ApplicationStatusHistory
Resume
ResumeParsingResult
ATSAnalysis
Integrity Rules
Unique user email
Unique saved job per user/job
Unique application per user/job
Unique stored resume filename
One parsing result per resume
One ATS analysis per resume/job pair
Company ownership enforcement
Foreign-key relationships with appropriate delete behavior
API Documentation

The complete API is available through Swagger:

https://jobportal-production-4e27.up.railway.app/docs

The API includes endpoints for:

Authentication
Users
Companies
Jobs
Applications
Saved jobs
Candidate profiles
Resumes
Candidate dashboard
Employer dashboard
ATS analysis
Local Setup
1. Clone the Repository
git clone https://github.com/ragulaanushaanu-cmd/Job_portal.git
cd Job_portal
2. Create a Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
3. Install Backend Dependencies
pip install -r requirements.txt
4. Configure Environment Variables

Copy:

.env.example

to:

.env

Example:

DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/job_portal

SECRET_KEY=YOUR_SECRET_KEY

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

Never commit .env.

5. Start the Backend
uvicorn main:app --reload

The API will be available at:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health
6. Start the Frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Vite will display the local frontend URL in the terminal.

Database Migrations

Alembic is used to manage database schema changes.

Apply Existing Migrations
alembic upgrade head
Create a New Migration

After changing SQLAlchemy models:

alembic revision --autogenerate -m "describe migration"

Then apply it:

alembic upgrade head
Fresh Database Note

The current migration history was developed incrementally and does not provide a complete zero-to-current bootstrap for a completely empty database.

For a fresh deployment database, the current schema can be created from the SQLAlchemy models and Alembic can then be marked at the current revision:

python -c "import models; from database import Base, engine; Base.metadata.create_all(bind=engine); print('Database schema created successfully')"

Then:

alembic stamp head

Future schema changes should continue to be managed through Alembic migrations.

Testing

The project currently contains 178 automated tests covering API behavior, authorization, dashboards, resume management, ATS functionality, and ATS service-level regression scenarios.

Run the complete test suite with:

python -m pytest tests/ -v

Current verified result:

178 passed

The ATS test coverage includes:

tests/test_ats.py
    API / integration coverage

tests/test_ats_service.py
    Detailed ATS service and regression coverage

GitHub Actions runs the backend test suite automatically for changes pushed to main.

Security

The project includes:

JWT authentication
bcrypt password hashing
Role-based access control
Resource ownership validation
Environment-based configuration
Global exception handling
Database integrity constraints
Resume file signature validation
Resume file size limits
Secure stored filenames
Hardened DOCX archive validation

Sensitive local files such as .env, uploaded files, virtual environments, generated frontend files, caches, and local test databases are excluded from version control.

Docker

The backend can be containerized using Docker.

Build the Image

Run from the project root:

docker build -t job-portal-backend .
Run the Container

For local Docker smoke testing:

docker run --name job-portal-backend-test -p 8000:8000 -e DATABASE_URL=sqlite:///./docker_test.db -e SECRET_KEY=docker-test-only-secret -e ALGORITHM=HS256 -e ACCESS_TOKEN_EXPIRE_MINUTES=30 job-portal-backend

The application will be available at:

http://localhost:8000

Health check:

http://localhost:8000/health

Swagger:

http://localhost:8000/docs

The Docker image uses environment variables for runtime configuration, allowing the same image to be used across different environments.

Docker Validation

The local Docker setup has been validated through:

Successful Docker image build
Successful container startup
Successful FastAPI application startup
Successful health check
Successful database connectivity
Production Deployment

The application is deployed on Railway with separate services for the backend and frontend.

GitHub Repository
        │
        ├── Job_portal
        │      └── FastAPI + Docker
        │
        ├── MySQL
        │
        └── acceptable-beauty
               └── React + Vite
Production Components
Frontend: React + Vite
Backend: FastAPI
Database: Railway MySQL
ORM: SQLAlchemy
Migrations: Alembic
Authentication: JWT + bcrypt
Authorization: Candidate / Employer / Admin RBAC
Resume parsing: PDF/DOCX
ATS analysis: Skill, experience, education, keyword and project matching
Resume storage: Railway Volume mounted at /app/uploads
CI: GitHub Actions
Containerization: Docker
Deployment Configuration

The backend uses Railway environment variables for:

DATABASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
FRONTEND_ORIGINS
UPLOAD_DIR

The frontend uses:

VITE_API_BASE_URL

The frontend service is deployed from the /frontend directory of the repository.

Production Verification

The deployed application has been verified through end-to-end candidate and employer workflows.

Candidate
Authentication
Candidate dashboard
Job browsing
Job details
Saved jobs
Resume upload
Resume download
Resume parsing
ATS analysis
Job application
Application tracking
Application status history
Employer
Authentication
Employer dashboard
Company creation
Job creation
Job management
Application review
Application status updates
Dashboard statistics
Cross-Role Verification

The following production workflow was successfully verified:

Candidate Login
      ↓
Browse Job
      ↓
Save Job
      ↓
Upload Resume
      ↓
Parse Resume
      ↓
ATS Analysis
      ↓
Apply for Job
      ↓
Employer Reviews Application
      ↓
Employer Shortlists Candidate
      ↓
Candidate Sees Updated Status
      ↓
Candidate Dashboard Updated
      ↓
Employer Dashboard Updated
Current Status

The Job Portal is deployed and operational on Railway.

Production frontend is live
Production backend is live
Railway MySQL is connected
Database schema is initialized
Resume persistence is configured with a Railway Volume
Candidate and Employer workflows have been verified
ATS analysis has been verified in production
GitHub Actions CI is passing
Backend test suite: 178 passing
Future Improvements

Possible future improvements include:

Repairing and consolidating the initial Alembic migration history so a completely empty database can be initialized with alembic upgrade head alone
More comprehensive operational monitoring and alerting
Additional production security hardening
Expanded automated end-to-end testing
Additional frontend UX and accessibility improvements

**Use this entire block as your `README.md`.**

One correction from the earlier version: the project structure and migration sections above are based on the structure we actually verified during deployment, rather than adding new architecture.

After saving the file, run only:

```powershell
git diff --check