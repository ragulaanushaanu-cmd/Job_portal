# Job Portal

A full-stack job portal built with **FastAPI, React, MySQL, SQLAlchemy, JWT authentication, role-based access control, resume parsing, and an ATS resume-to-job matching system**.

The project is designed as a production-oriented portfolio application demonstrating backend architecture, database design, authentication and authorization, API development, automated testing, and practical ATS logic.

---

## Overview

The Job Portal connects candidates and employers through a single full-stack platform.

### Candidate workflow

Candidates can:

* Register and authenticate securely
* Maintain their candidate profile
* Browse and search available jobs
* Filter jobs by relevant criteria
* Save jobs for later
* Upload and manage resumes
* Set a primary resume
* Apply for jobs
* Track application status and history
* Analyze a resume against a job using the ATS system

### Employer workflow

Employers can:

* Authenticate through the same platform
* Create and manage companies
* Create, edit, and delete their jobs
* View applications submitted to their jobs
* Update application statuses
* View employer dashboard information
* Manage company and job information

---

## Key Features

### Authentication & Authorization

* JWT-based authentication
* Password hashing with bcrypt
* Role-based access control
* Candidate, Employer, and Admin roles
* Protected API endpoints using FastAPI dependencies
* Ownership checks for user-specific resources

### Job Management

* Job creation and management
* Search and filtering
* Location filtering
* Salary information
* Employment type
* Experience level
* Work mode
* Pagination
* Sorting
* Employer ownership validation

### Resume Management

* Resume upload
* Resume listing
* Resume download
* Primary resume selection
* Resume deletion
* Resume parsing
* Parser version tracking
* Structured parsed resume data

### Applications

* Candidate job applications
* Resume selection during application
* Application status tracking
* Application status history
* Candidate access control
* Employer access control
* Protection against duplicate applications

### Candidate Profile

* Candidate headline
* Bio
* Phone and location
* Experience
* Education
* Skills
* LinkedIn
* GitHub
* Portfolio

### Saved Jobs

* Save jobs
* List saved jobs
* Remove saved jobs
* Duplicate-save protection

### Dashboards

Candidate dashboard includes application-related information and saved-job data.

Employer dashboard includes:

* Owned companies
* Job totals
* Application statistics
* Recent applications
* Application status breakdown

---

# ATS Resume Matching System

One of the main features of this project is the ATS-style resume analysis system.

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
```

## ATS Scoring

The current scoring model uses:

| Component  | Weight |
| ---------- | -----: |
| Skills     |    40% |
| Keywords   |    25% |
| Experience |    20% |
| Education  |    15% |

The final result includes:

* Overall ATS score
* Skill score
* Keyword score
* Experience score
* Education score
* Matched skills
* Missing skills
* Matched keywords
* Missing keywords
* Recommendations

### ATS engineering details

The ATS implementation includes:

* Skill canonicalization and alias handling
* Phrase-aware matching
* Singular/plural keyword normalization
* Meaningful keyword filtering
* Generic keyword rejection
* Technical-skill exclusion from ordinary keyword extraction
* Education hierarchy handling
* Education field/specialization matching
* Required experience extraction
* Project relevance based on ATS keywords
* Duplicate canonical keyword protection
* Recommendation generation based on detected gaps
* Parser-version readiness validation
* Resume ownership validation
* Unique resume/job ATS analysis handling

---

# Architecture

The application follows a layered backend architecture.

```text
React Frontend
      ↓
FastAPI Routers
      ↓
Service Layer
      ↓
SQLAlchemy ORM
      ↓
MySQL Database
```

Cross-cutting concerns include:

```text
Authentication
Authorization / RBAC
Validation
Error Handling
Database Transactions
File Handling
Pagination
Logging
```

The backend separates HTTP/API responsibilities from business logic through routers and services.

---

# Technology Stack

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* MySQL
* PyMySQL
* Alembic
* python-jose
* Passlib / bcrypt
* python-dotenv
* Uvicorn

## Frontend

* React
* Vite
* Axios
* JavaScript
* React Router

## Testing

* pytest
* FastAPI TestClient
* SQLite-based isolated test database
* GitHub Actions

---

# Project Structure

```text
job_portal/
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
```

---

# Database Design

The application uses MySQL with SQLAlchemy ORM and Alembic migrations.

Major entities include:

```text
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
```

Important integrity rules include:

* Unique user email
* Unique saved job per user/job
* Unique application per user/job
* Unique stored resume filename
* One parsing result per resume
* One ATS analysis per resume/job pair
* Company ownership enforcement
* Foreign-key relationships with appropriate delete behavior

---

# API Documentation

When running locally, FastAPI provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/ragulaanushaanu-cmd/Job_portal.git
cd Job_portal
```

## 2. Create and activate a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then configure the local values.

Example:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/job_portal
SECRET_KEY=YOUR_SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit `.env`.

## 5. Start the backend

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## 6. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite will display the local frontend URL in the terminal.

---

# Database Migrations

Alembic is used for schema migrations.

To apply available migrations:

```bash
alembic upgrade head
```

To create a new migration after a model change:

```bash
alembic revision --autogenerate -m "describe migration"
```

Then apply it:

```bash
alembic upgrade head
```

---

# Testing

The project currently contains **178 automated tests** covering API behavior, authorization, dashboards, resume management, ATS functionality, and ATS service-level regression scenarios.

Run the complete suite with:

```powershell
python -m pytest tests/ -v
```

Current verified result:

```text
178 passed
```

The ATS test coverage includes both:

```text
tests/test_ats.py
    API / integration coverage

tests/test_ats_service.py
    detailed ATS service and regression coverage
```

---

# Security

The project uses:

* JWT authentication
* bcrypt password hashing
* Role-based access control
* Resource ownership validation
* Environment-based configuration
* Global exception handling
* Database integrity constraints

Sensitive local files such as `.env`, uploaded files, virtual environments, generated frontend files, caches, and local test databases are excluded from version control.

---

# Current Status

The project currently has:

* FastAPI backend
* React frontend
* MySQL database integration
* Alembic migrations
* JWT authentication
* Candidate / Employer / Admin roles
* Candidate dashboard
* Employer dashboard
* Job management
* Saved jobs
* Applications and status history
* Resume management
* Resume parsing
* ATS resume-to-job analysis
* 178 automated tests
* GitHub Actions CI
* Docker backend packaging
* GitHub repository

Production deployment, hosting configuration, structured production logging, monitoring, and further security hardening remain part of the production delivery phase.

---

## Docker

The backend can be containerized and run using Docker.

### Docker image

Build the backend image from the project root:

```bash
docker build -t job-portal-backend .
```

### Run the container

For local Docker smoke testing, the backend can be run with a temporary SQLite database:

```powershell
docker run --name job-portal-backend-test `
  -p 8000:8000 `
  -e DATABASE_URL=sqlite:///./docker_test.db `
  -e SECRET_KEY=docker-test-only-secret `
  -e ALGORITHM=HS256 `
  -e ACCESS_TOKEN_EXPIRE_MINUTES=30 `
  job-portal-backend
```

The application is available at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Swagger documentation:

```text
http://localhost:8000/docs
```

The Docker image uses environment variables for runtime configuration, allowing the same image to be used with different database and application settings across environments.

The Docker setup has been validated through:

* Successful Docker image build
* Successful container startup
* Successful FastAPI application startup
* Successful health check
* Successful database connectivity

---

# Future Improvements

Planned production improvements include:

* Production frontend and backend hosting
* Production CORS configuration
* Structured production logging
* Deployment documentation
* Additional operational monitoring
* Further security hardening

---

# Author

**Anusha Ragula**

GitHub:

https://github.com/ragulaanusha-cmd