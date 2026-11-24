# Personal Finance Manager (SQL Server Desktop)

Windows desktop starter application using **PySide6** and **Microsoft SQL Server** as its backend.

## Included in Version 1
- Dashboard totals for monthly income/expenses, loans, credit cards, money lent/borrowed, net cash flow
- Transaction income/expense register
- Loan register (principal, balance, ROI, EMI, due day, tenure)
- Credit card register (limit, outstanding, statement/due dates)
- Udhar ledger (Lent / Borrowed, person, original/balance, ROI, expected date)
- Accounts register (bank/cash/wallet/investment accounts)
- CRUD (add/edit/delete), SQL Server schema initialization, editable connection string, Windows authentication support

## Requirements
- Windows 10/11
- Python 3.10+ (64-bit recommended)
- Microsoft ODBC Driver 17 or 18 for SQL Server
- SQL Server / SQL Server Express / SQL Server Developer edition and permission to create tables in the target database

## Setup
1. Install SQL Server and create a database named `PersonalFinance` (or choose your own database).
2. Install the Microsoft ODBC Driver for SQL Server.
3. Install Python 3.10+.
4. Extract this folder.
5. In this folder, run `setup.bat` (creates venv, installs dependencies, copies config template).
6. Run `run.bat`.
7. From the app menu, choose **Database → Configure SQL Server…**. Update the server/instance and database in the connection string, click **Test Connection**, then **Save**.
8. Choose **Database → Initialize / Verify Tables** to create the tables.

Example connection string (Windows integrated authentication):
`DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=PersonalFinance;Trusted_Connection=yes;TrustServerCertificate=yes;`

For a default SQL Server instance use `SERVER=localhost`; for another server use its hostname or `hostname,port`.

## Important
- This is a local personal finance app. Keep the database backed up and restrict database permissions.
- Dashboard figures are based on data entered in this app. Loan balances and card balances are manual snapshots in v1; payment schedules and automatic bank feeds are planned enhancements.
- Avoid storing full card numbers, passwords, CVV, or sensitive credentials. Store a nickname only.
- Amounts use INR display conventions in the UI.

## Project files
- `app.py`: desktop GUI and CRUD modules
- `db.py`: SQL Server connectivity
- `schema.sql`: table definitions
- `requirements.txt`: Python dependencies
- `config.ini.example`: example connection configuration
