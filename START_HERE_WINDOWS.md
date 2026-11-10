# Golden Gym V4.1 — Windows quick start

1. Extract this ZIP to a normal folder, for example `D:\Golden_Gym_V4.1`.
2. Open PowerShell in that folder.
3. Create and activate a virtual environment:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Create your local environment file:

```powershell
Copy-Item .env.example .env
```

5. Open `.env`. Set a long private `SECRET_KEY`. For online payments, enter your own Cashfree Sandbox credentials or Razorpay test credentials. Do not share or commit `.env`.
6. Apply the database migration and run checks:

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

7. Open `http://127.0.0.1:8000/`.

## Important payment setup

The public membership plan cards link to registration. Registration then opens Cashfree hosted checkout when Cashfree credentials are configured; Razorpay is the fallback when its credentials are configured. If neither gateway is configured, the site clearly tells the member that online checkout is not available and leaves the membership pending. Successful payment is activated only after server-side verification.

Start with gateway Sandbox/Test credentials. Do not accept real payments until merchant onboarding, HTTPS, webhook delivery, and end-to-end success/failure/duplicate-payment tests are complete.

## New owner pages

After signing in as an owner:
- `/dashboard/inventory/`
- `/dashboard/expenses/`
- `/dashboard/staff/`
- Member list → Print card

The staff directory stores staff contact/role information; it does not create staff login accounts. The inventory and expense pages currently provide create-and-view workflows.

## Existing database

The supplied `db_v21.sqlite3` is retained in the ZIP. Back it up before running migrations or replacing it with another database. The new migration is `0009_owner_operations`.
