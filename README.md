# DealerOS - Data Reconciliation Dashboard



## 1. Project Overview



DealerOS is a data reconciliation dashboard that compares records from two independent systems (System A and System B), identifies inconsistencies, and displays the results in an organization-filtered dashboard.



The application imports CSV datasets, normalizes record references, performs reconciliation, identifies different types of disagreements, and provides a React-based interface to review the results.



## 2. Technology Stack



| Component | Technology |

|---|---|

| Backend | Python 3.13 |

| Backend Framework | Django 5.2 |

| API | Django REST Framework |

| Frontend | React |

| Frontend Build Tool | Vite |

| Programming Languages | Python, JavaScript |

| Styling | CSS |

| Database | SQLite |

| Input Data | CSV files |

| Version Control | Git |



## 3. Main Features



\- Imports location, System A, and System B CSV records.

\- Preserves source values and row information during import.

\- Normalizes inconsistent record references.

\- Handles blank values and comma-separated numeric amounts.

\- Detects records missing from System B.

\- Detects orphan records in System B.

\- Identifies duplicate entries in System B.

\- Detects value mismatches.

\- Detects date and location mismatches.

\- Supports valid split entries when multiple System B entries correctly match a System A total.

\- Identifies records associated with VOIDED entries.

\- Supports organization-based filtering.

\- Supports filtering by disagreement reason.

\- Sorts disagreement records by value in ascending or descending order.

\- Redacts opposing-system details for cross-tenant mismatches.

\- Provides a dashboard for reviewing disagreement records.



## 4. Project Structure



```text

DealerOS/

â”‚

â”œâ”€â”€ backend/

â”‚   â”œâ”€â”€ config/

â”‚   â”‚   â”œâ”€â”€ settings.py

â”‚   â”‚   â””â”€â”€ urls.py

â”‚   â”‚

â”‚   â”œâ”€â”€ reconcile/

â”‚   â”‚   â”œâ”€â”€ management/

â”‚   â”‚   â”‚   â””â”€â”€ commands/

â”‚   â”‚   â”‚       â””â”€â”€ import\_dealer\_data.py

â”‚   â”‚   â”œâ”€â”€ migrations/

â”‚   â”‚   â”œâ”€â”€ models.py

â”‚   â”‚   â”œâ”€â”€ serializers.py

â”‚   â”‚   â”œâ”€â”€ services.py

â”‚   â”‚   â”œâ”€â”€ tests.py

â”‚   â”‚   â”œâ”€â”€ urls.py

â”‚   â”‚   â””â”€â”€ views.py

â”‚   â”‚

â”‚   â”œâ”€â”€ requirements.txt

â”‚   â””â”€â”€ manage.py

â”‚

â”œâ”€â”€ frontend/

â”‚   â”œâ”€â”€ src/

â”‚   â”‚   â”œâ”€â”€ App.jsx

â”‚   â”‚   â”œâ”€â”€ App.css

â”‚   â”‚   â””â”€â”€ index.css

â”‚   â”œâ”€â”€ package.json

â”‚   â”œâ”€â”€ package-lock.json

â”‚   â””â”€â”€ vite.config.js

â”‚

â”œâ”€â”€ data/

â”‚   â””â”€â”€ raw/

â”‚       â””â”€â”€ DealerOS\_Assignment\_Dataset/

â”‚           â”œâ”€â”€ locations.csv

â”‚           â”œâ”€â”€ system\_a.csv

â”‚           â””â”€â”€ system\_b.csv

â”‚

â”œâ”€â”€ venv/

â”œâ”€â”€ .gitignore

â”œâ”€â”€ README.md

â””â”€â”€ DECISIONS.md

```



## 5. Requirements



Install the following before running the project:



\- Python 3.13

\- Node.js and npm

\- Git



## 6. Backend Setup and Execution



Open PowerShell in the project root directory.



### Step 1: Create and activate the virtual environment



```powershell

py -3.13 -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



### Step 2: Install Python dependencies



```powershell

python -m pip install -r backend/requirements.txt

```



### Step 3: Navigate to the backend directory



```powershell

cd backend

```



### Step 4: Apply database migrations



```powershell

python manage.py migrate

```



### Step 5: Import the CSV dataset



```powershell

python manage.py import\_dealer\_data

```



### Step 6: Run reconciliation



```powershell

python manage.py shell -c "from reconcile.services import run\_reconciliation; print('Disagreements created:', run\_reconciliation())"

```



### Step 7: Start the Django development server



```powershell

python manage.py runserver

```



Backend server:



`http://127.0.0.1:8000/`



API endpoint:



`http://127.0.0.1:8000/api/disagreements/?org\_id=ORG-A`



Keep the backend terminal running while using the frontend.



## 7. Frontend Setup and Execution



Open a second PowerShell terminal in the project root.



### Step 1: Navigate to the frontend directory



```powershell

cd frontend

```



### Step 2: Install frontend dependencies



```powershell

npm install

```



### Step 3: Start the React development server



```powershell

npm run dev

```



Open the local URL displayed by


