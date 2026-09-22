# BloodAid --- Blood Donation & Emergency Assistance

BloodAid is a full-stack blood donation and emergency blood request
platform.

The project has:

-   **Frontend:** React + Vite + Tailwind CSS + DaisyUI
-   **Backend:** FastAPI + SQLAlchemy
-   **Database:** PostgreSQL on Supabase
-   **Backend hosting:** Render
-   **Frontend hosting:** Netlify
-   **Authentication:** JWT access/refresh tokens
-   **API documentation:** FastAPI Swagger UI

------------------------------------------------------------------------

## 1. Project Features

### User

-   Register and login
-   JWT authentication
-   View personal dashboard
-   Create blood requests
-   View own blood requests
-   Edit own blood requests
-   Delete own blood requests
-   View request details

### Donor

-   Register as a donor
-   View donor dashboard
-   View available blood requests
-   Respond to blood requests
-   View own donation responses
-   Manage donor availability

### Admin

-   Admin dashboard
-   View total users
-   View total donors
-   View available donors
-   View blood requests
-   View donation responses
-   Edit users
-   Delete users
-   Edit donors
-   Delete donors
-   Change donor availability
-   Change request status
-   Change donation response status
-   Delete requests
-   Delete donation responses

------------------------------------------------------------------------

# 2. Project Structure

The recommended GitHub structure is:

``` text
BloodAid/
│
├── backend/
│   ├── router/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── admin.py
│   │
│   ├── database.py
│   ├── models.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── netlify.toml
│   ├── .env.example
│   └── .gitignore
│
└── README.md
```

You can also keep backend and frontend in two separate GitHub
repositories. For a beginner-friendly deployment workflow, separate
repositories are often easier:

``` text
bloodaid-backend
bloodaid-frontend
```

The instructions below assume **two repositories**.

------------------------------------------------------------------------

# 3. Backend Requirements

Install the backend dependencies:

``` bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv passlib bcrypt python-jose python-multipart pydantic[email]
```

Your `requirements.txt` should contain the packages your project
actually imports. For example:

``` txt
fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
passlib
bcrypt
python-jose
python-multipart
pydantic[email]
```

If you already have a working `requirements.txt`, keep the versions you
have tested locally.

------------------------------------------------------------------------

# 4. Backend Environment Variables

Do **not** upload your real `.env` file to GitHub.

Create:

``` text
.env.example
```

Example:

``` env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres
SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://localhost:5173
```

The real `.env` file stays on your computer and should be ignored by
Git.

------------------------------------------------------------------------

# 5. Change SQLite to Supabase PostgreSQL

The current local project uses:

``` python
sqlite:///./blood_donation.db
```

For production, use the PostgreSQL connection string from Supabase.

A deployment-friendly `database.py` should use an environment variable:

``` python
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

Base = declarative_base()
```

For Supabase, open your project and use the database connection string
from:

**Supabase Dashboard → Connect → PostgreSQL**

Use the connection method appropriate for your deployment. Supabase
provides direct and pooled connection options.

If your password contains special characters such as `@`, `#`, `?`, `&`,
or spaces, URL-encode the password before putting it in the connection
URL.

------------------------------------------------------------------------

# 6. Important Backend CORS Change

Your local frontend currently uses:

``` text
http://localhost:5173
```

After Netlify deployment, your frontend will have a URL similar to:

``` text
https://your-site.netlify.app
```

The backend must allow that production frontend origin.

For example:

``` python
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://your-site.netlify.app"
]
```

Then:

``` python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

Replace:

``` text
https://your-site.netlify.app
```

with your actual Netlify URL.

------------------------------------------------------------------------

# 7. JWT Secret

Do not keep a production JWT secret directly in your source code.

Instead of:

``` python
SECRET_KEY = "your-secret"
```

use an environment variable:

``` python
import os

SECRET_KEY = os.getenv("SECRET_KEY")
```

Then set the real value in Render.

Generate a strong secret instead of using:

``` text
admin
password
123456
```

------------------------------------------------------------------------

# 8. Admin Credentials

The development project currently creates an admin with:

``` text
username: admin
password: admin
```

Do not use these credentials for a real production system.

Before making the project public, change the admin creation process so
the production admin has a strong password.

------------------------------------------------------------------------

# 9. Create Supabase Database

1.  Open Supabase.
2.  Create a new project.
3.  Choose a strong database password.
4.  Wait until the project is ready.
5.  Open **Connect**.
6.  Copy the PostgreSQL connection string.
7.  Put that connection string into your local `.env`.
8.  Test the backend locally.

Example:

``` env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres
```

Do not commit this value to GitHub.

------------------------------------------------------------------------

# 10. Test Backend Locally With Supabase

After changing `database.py`:

``` bash
cd backend
```

Activate your virtual environment.

Then run:

``` bash
uvicorn main:app --reload
```

Open:

``` text
http://127.0.0.1:8000/docs
```

Test:

-   Register
-   Login
-   `/auth/me`
-   Create request
-   View request
-   Donor response
-   Admin dashboard

If these work, the backend is ready for Render.

------------------------------------------------------------------------

# 11. Backend `.gitignore`

Create:

``` text
backend/.gitignore
```

Use:

``` gitignore
__pycache__/
*.py[cod]
*.pyo

.venv/
venv/
env/

.env

*.db
*.sqlite
*.sqlite3

.pytest_cache/
.coverage
htmlcov/

.idea/
.vscode/

.DS_Store
```

Important:

``` text
.env
```

must be ignored.

Do not upload:

-   database passwords
-   JWT secrets
-   API keys
-   `.env`
-   local SQLite database

------------------------------------------------------------------------

# 12. Push Backend to GitHub

From the backend directory:

``` bash
git init
```

Then:

``` bash
git add .
```

Commit:

``` bash
git commit -m "Initial BloodAid backend"
```

Create a GitHub repository, for example:

``` text
bloodaid-backend
```

Then connect it:

``` bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bloodaid-backend.git
git push -u origin main
```

------------------------------------------------------------------------

# 13. Deploy Backend to Render

Open Render and connect your GitHub account.

Create:

``` text
New → Web Service
```

Select:

``` text
bloodaid-backend
```

Use:

``` text
Language:
Python 3
```

Build command:

``` bash
pip install -r requirements.txt
```

Start command:

``` bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

If your backend is inside a monorepo, set the Render Root Directory to:

``` text
backend
```

Then add environment variables in Render.

Example:

``` text
DATABASE_URL=your_supabase_postgresql_connection_string

SECRET_KEY=your_production_secret

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=300

REFRESH_TOKEN_EXPIRE_DAYS=7

FRONTEND_URL=https://your-site.netlify.app
```

Deploy the service.

Render will give you a URL similar to:

``` text
https://bloodaid-backend.onrender.com
```

Test:

``` text
https://bloodaid-backend.onrender.com/
```

and:

``` text
https://bloodaid-backend.onrender.com/docs
```

------------------------------------------------------------------------

# 14. Frontend API URL

Your current frontend has:

``` text
src/services/BaseUrl.jsx
```

Change it so the production API URL can come from an environment
variable.

For Vite:

``` jsx
export const baseUrl =
    import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
```

For local development, create:

``` text
frontend/.env
```

``` env
VITE_API_URL=http://127.0.0.1:8000
```

Do not commit the `.env` file if you want to keep environment
configuration out of Git.

Create:

``` text
frontend/.env.example
```

``` env
VITE_API_URL=http://127.0.0.1:8000
```

------------------------------------------------------------------------

# 15. Important Vite Environment Variable Rule

Because this is a Vite React application, browser-exposed environment
variables use the:

``` text
VITE_
```

prefix.

Correct:

``` env
VITE_API_URL=https://bloodaid-backend.onrender.com
```

Then access it with:

``` javascript
import.meta.env.VITE_API_URL
```

Do not put private backend secrets in frontend environment variables.

Anything included in the frontend build can ultimately be visible to
users.

------------------------------------------------------------------------

# 16. Frontend `.gitignore`

Create:

``` text
frontend/.gitignore
```

Use:

``` gitignore
node_modules/
dist/

.env
.env.local
.env.development.local
.env.test.local
.env.production.local

.vscode/
.idea/

.DS_Store
```

------------------------------------------------------------------------

# 17. Test Frontend Locally

From the frontend directory:

``` bash
npm install
```

Then:

``` bash
npm run dev
```

Open:

``` text
http://localhost:5173
```

Make sure:

-   Login works
-   Signup works
-   User dashboard works
-   Create request works
-   Donor dashboard works
-   Donor can see blood requests
-   Donor can respond
-   Admin dashboard works
-   Admin can edit users
-   Admin can edit donors
-   Admin can update availability
-   Admin can update request status
-   Admin can update response status

------------------------------------------------------------------------

# 18. Push Frontend to GitHub

From the frontend directory:

``` bash
git init
```

Then:

``` bash
git add .
```

Commit:

``` bash
git commit -m "Initial BloodAid frontend"
```

Create:

``` text
bloodaid-frontend
```

on GitHub.

Then:

``` bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bloodaid-frontend.git
git push -u origin main
```

------------------------------------------------------------------------

# 19. Deploy Frontend to Netlify

Open Netlify.

Choose:

``` text
Add new project
```

Then:

``` text
Import an existing project
```

Connect GitHub.

Select:

``` text
bloodaid-frontend
```

Because the project uses Vite, use:

``` text
Build command:
npm run build
```

Publish directory:

``` text
dist
```

Netlify normally detects these Vite settings automatically.

------------------------------------------------------------------------

# 20. Netlify Environment Variable

In Netlify:

``` text
Project configuration
→ Environment variables
```

Create:

``` text
VITE_API_URL
```

Value:

``` text
https://bloodaid-backend.onrender.com
```

Use your actual Render URL.

Then redeploy the frontend.

------------------------------------------------------------------------

# 21. React Router + Netlify

Your project uses React Router.

For example:

``` text
/login
/signup
/user/dashboard
/donor/dashboard
/admin/dashboard
```

If someone directly opens:

``` text
https://your-site.netlify.app/admin/dashboard
```

Netlify needs to serve your React application's `index.html`.

Create:

``` text
frontend/netlify.toml
```

with:

``` toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

This prevents React Router routes from returning Netlify 404 pages.

------------------------------------------------------------------------

# 22. Final Deployment Architecture

Your finished project will look like:

``` text
                    USER
                      |
                      v
             ┌─────────────────┐
             │     Netlify     │
             │ React + Vite    │
             └────────┬────────┘
                      |
                      | HTTPS API requests
                      v
             ┌─────────────────┐
             │     Render      │
             │    FastAPI      │
             └────────┬────────┘
                      |
                      | PostgreSQL
                      v
             ┌─────────────────┐
             │    Supabase     │
             │   PostgreSQL    │
             └─────────────────┘
```

GitHub:

``` text
GitHub
│
├── bloodaid-frontend
│       │
│       └── Netlify
│
└── bloodaid-backend
        │
        └── Render
                │
                └── Supabase PostgreSQL
```

------------------------------------------------------------------------

# 23. Deployment Order

Follow this exact order:

### Step 1

Create Supabase project.

### Step 2

Get the Supabase PostgreSQL connection string.

### Step 3

Change backend `database.py` to use:

``` text
DATABASE_URL
```

### Step 4

Test FastAPI locally against Supabase.

### Step 5

Add production-safe JWT secret through environment variables.

### Step 6

Update backend CORS to allow the future Netlify domain.

### Step 7

Push backend to GitHub.

### Step 8

Deploy backend to Render.

### Step 9

Test:

``` text
https://YOUR-RENDER-URL/docs
```

### Step 10

Update frontend `BaseUrl.jsx` to use:

``` text
VITE_API_URL
```

### Step 11

Test frontend locally using the Render API.

### Step 12

Push frontend to GitHub.

### Step 13

Deploy frontend to Netlify.

### Step 14

Set Netlify:

``` text
VITE_API_URL=https://YOUR-RENDER-URL
```

### Step 15

Add `netlify.toml` for React Router.

### Step 16

Copy the final Netlify URL.

### Step 17

Add that Netlify URL to FastAPI CORS.

### Step 18

Redeploy Render.

### Step 19

Test the complete application.

------------------------------------------------------------------------

# 24. Final Production Checklist

## GitHub

-   [ ] Backend repository created
-   [ ] Frontend repository created
-   [ ] `.env` not committed
-   [ ] Database credentials not committed
-   [ ] JWT secret not committed
-   [ ] SQLite database not committed
-   [ ] `node_modules` not committed
-   [ ] `dist` not committed

## Supabase

-   [ ] Project created
-   [ ] PostgreSQL connection tested
-   [ ] Correct database password used
-   [ ] Backend can create/read database tables

## Render

-   [ ] GitHub backend connected
-   [ ] Python selected
-   [ ] Build command correct
-   [ ] Start command correct
-   [ ] `DATABASE_URL` added
-   [ ] `SECRET_KEY` added
-   [ ] Other required environment variables added
-   [ ] `/docs` works
-   [ ] `/` works

## Netlify

-   [ ] GitHub frontend connected
-   [ ] Build command `npm run build`
-   [ ] Publish directory `dist`
-   [ ] `VITE_API_URL` configured
-   [ ] `netlify.toml` added
-   [ ] React Router URLs work

## Final application

-   [ ] Signup works
-   [ ] Login works
-   [ ] Logout works
-   [ ] User dashboard works
-   [ ] User can create request
-   [ ] User can edit request
-   [ ] User can delete request
-   [ ] Donor dashboard works
-   [ ] Donor can see blood requests
-   [ ] Donor can respond
-   [ ] Donor can see responses
-   [ ] Admin login works
-   [ ] Admin dashboard works
-   [ ] Admin can manage users
-   [ ] Admin can manage donors
-   [ ] Admin can change donor availability
-   [ ] Admin can manage requests
-   [ ] Admin can manage responses

------------------------------------------------------------------------

# 25. Useful URLs After Deployment

Frontend:

``` text
https://YOUR-SITE.netlify.app
```

Backend:

``` text
https://YOUR-BACKEND.onrender.com
```

Swagger API documentation:

``` text
https://YOUR-BACKEND.onrender.com/docs
```

ReDoc:

``` text
https://YOUR-BACKEND.onrender.com/redoc
```

------------------------------------------------------------------------

## License

This project is created for educational and portfolio purposes.

------------------------------------------------------------------------

## Author

**Your Name**

BloodAid --- Blood Donation & Emergency Assistance
