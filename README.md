# Golden Gym V4.0 — Gym management platform with Cashfree checkout

A separate upgrade of Golden Gym V2. The original V1 and V2 folders are not modified by this package.


## V3.0 improvements

- Fixed the public mobile navigation initialization so the Membership link can be opened on phones. The old shared script returned early when the staff dashboard menu was absent; the public and staff menus now initialize independently.
- Reworked the membership cards for phone screens into a swipeable, snap-aligned plan rail with clearer pricing, features and full-width join actions. Desktop membership layout remains unchanged.
- Improved mobile navigation accessibility with expanded state, close-on-section-selection and Escape-key support.
- Kept existing membership registration, plan lookup, Razorpay checkout, payment verification and membership activation logic unchanged.
- V3.0 is packaged as a separate folder; the original V1, V2 and V2.1 project folders are not overwritten.

## Included V2.1 upgrades

1. **UPI / Razorpay checkout** — UPI is explicitly enabled in Razorpay Checkout where the merchant account supports it. The server verifies the checkout signature, fetches the payment, checks order ID, amount and captured status, then activates the membership.
2. **Owner analytics** — member/active/pending/expiry counters, monthly and year-to-date revenue, recent payments/enquiries and a monthly revenue chart.
3. **QR attendance** — each member has a unique QR token and a downloadable-on-screen pass; owner or assigned trainer can scan at reception. A same-day duplicate check-in is blocked.
4. **Workout management** — exercise library, workout plans, trainer assignment and sets/reps/rest prescriptions. Trainers can manage their own plans and assigned members.
5. **Fitness tracking** — member measurement history and personal goals.
6. **Membership renewal** — online renewal reuses the active plan and extends the membership from the later of today or the existing expiry date.
7. **Notifications** — in-app payment and expiry notices; a daily management command marks expired memberships and creates reminders. SMTP email is optional.
8. **Reports** — owner can export member, payment and attendance data to Excel or PDF.
9. **Mobile-first responsive refinement** — adaptive navigation for owner/staff dashboards, responsive portal cards, touch-sized controls, contained horizontal table scrolling, compact layouts for 320px phones, and reduced-motion support. The public website, owner dashboard, trainer portal and member portal share the responsive stylesheet.
10. **Member account settings** — edit personal contact details/photo and change password.
11. **Offline-friendly operations** — staff can register members manually, record attendance from the reception form without requiring a member smartphone, and record cash, UPI, card/POS, bank-transfer or verified gateway payments. Manual and QR attendance now prevent same-day duplicate check-ins and reject inactive/expired memberships.
12. **Member reference number** — the owner member list displays a simple reference such as `GG-000123` for reception lookup.

## Setup (Windows PowerShell)

Open this extracted folder in VS Code. Run commands from the folder containing `manage.py`.

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver 8002
```

If PowerShell blocks activation for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Use `python -m pip`, not `pip`, on systems where Application Control blocks `pip.exe`.

Open:
- Public website: http://127.0.0.1:8002/
- Common login: http://127.0.0.1:8002/accounts/login/
- Owner dashboard: http://127.0.0.1:8002/dashboard/
- Django Admin: http://127.0.0.1:8002/admin/

Use port 8002 so V2 can remain on 8001 and V1 can remain on 8000.

## Roles

- **Owner:** create the first superuser with `createsuperuser`; it is treated as the owner.
- **Member:** register through a membership plan on the public website, or have staff create a record from Dashboard → Members → Add member. A member smartphone is not required for staff-managed attendance or payments. Member login redirects to the member portal.
- **Trainer:** owner creates a trainer login from Dashboard → Trainers. Assign members and trainer access through Django Admin → Trainers. Trainer login redirects to trainer portal.
- All roles use the same login page. Role is assigned by the system/owner, not selected by the person logging in.

## Razorpay / UPI test configuration

1. Create or use the gym owner's Razorpay merchant account.
2. Put the Razorpay **test** Key ID and Key Secret in `.env`:
   `RAZORPAY_KEY_ID=rzp_test_...`
   `RAZORPAY_KEY_SECRET=...`
3. Confirm UPI is enabled for the merchant account in Razorpay settings.
4. Restart Django and test checkout using Razorpay test mode.
5. Confirm a successful payment produces a paid record, receipt, membership period and active membership.
6. Test failed, cancelled, wrong-amount and duplicate submissions before switching to live credentials.

The app cannot collect money until the merchant account credentials are configured. Actual UPI apps and live settlement were not tested in this build. Razorpay availability and enabled methods depend on the merchant account and gateway policy. A dedicated Razorpay webhook endpoint is not included yet; add and verify webhooks before production for asynchronous payment reconciliation.

## Receipts and reports

- Members download their own paid payment receipt from their Member Portal.
- Owners export member, payment and attendance reports from Dashboard → Reports.
- PDF and XLSX exports are generated on demand.
- The QR scanner and revenue chart load their browser libraries from public CDNs; internet access is required for those visual widgets. Members without a smartphone can be checked in by staff using the reception attendance form. The same-day duplicate check applies to both QR and manual check-ins.

## Daily expiry notifications

Run this command once per day:

```powershell
python manage.py send_gym_notifications
```

For automatic daily execution on Windows, create a Windows Task Scheduler task that runs the command from this project folder using the virtual environment's Python executable (`venv\Scripts\python.exe`). Configure SMTP values in `.env` if email delivery is required. Without SMTP, reminders remain in the member's in-app notification list.

## Database and preservation

- V2.1 uses `db_v21.sqlite3` by default because `.env.example` sets `DB_NAME=db_v21.sqlite3`.
- The ZIP intentionally excludes `.env`, the previous SQLite database, virtual environment and Python cache files.
- Existing V2 records are not copied automatically. Keep V2 untouched. If you later need to migrate real member/payment records, take a backup and plan a separate data migration.

## Responsive testing targets

Check the public website and all three portals at 320, 360, 390, 430, 768, 1024, 1280 and 1440px widths. Confirm there is no page-level horizontal overflow, navigation remains usable, forms fit the viewport, dashboard cards reflow, and wide tables scroll only inside their own containers. Physical-device/browser visual QA is still required before production.

## Verification completed for the original V2.1 baseline

- Django system checks passed using Django 6.0.10.
- Migrations 0001–0004 applied successfully to a separate test database. The mobile-first refinement adds migration 0005 for the card/POS payment method; apply it with `python manage.py migrate`.
- Demo seed command completed.
- HTTP smoke tests returned 200 for public home, owner pages, member portal, QR pass, profile, fitness page, trainer portal, attendance, workout page and PDF/Excel report endpoints.
- Additional workflow checks passed for member redirect, QR attendance, fitness measurement/goal saves, workout creation, PDF receipt download and password-change page.
- The current container cannot install Django dependencies because network access is unavailable, so the new migration and responsive changes have not been rerun through Django/browser integration tests here. Run `python manage.py check` and `python manage.py migrate` locally, then complete the responsive width checks above.

## Before production

This is a tested development build, not a production certification. Configure a strong `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS, SMTP and Razorpay live credentials. Test on the actual hosting platform and devices, review access permissions, configure a daily scheduler, and test real payment success/failure/refund/webhook handling. Do not share `.env` or API secrets.


## V3.0 validation notes

The public navigation script was reviewed and corrected, and the project Python files were syntax-compiled during packaging. The mobile membership layout is implemented with CSS scroll snapping and a single-column card presentation per swipe. Run the Django checks and test the public page at 320, 360, 390, 430, 768, 1024, 1280 and 1440px in your browser. Real device/browser QA and payment-provider testing are still required; do not treat this package as production-certified.


## V3.0.1 additive payment and member-access update

- Added owner-entered **Registered member** and **Walk-in / non-member** payment types. Walk-in payer name is required; phone number is optional.
- Walk-in payments can be recorded as cash, UPI, card/POS, bank transfer or pending/paid records using the existing payment method/status fields. A paid walk-in payment does not create or activate a membership.
- Added owner-downloadable PDF receipts for counter payments, including walk-in receipts. Payment exports now include walk-in payer names.
- Member phone number is optional for staff-created member records and online signup. Existing phone values are preserved.
- Existing Razorpay membership signup/renewal checkout and server-side signature, order, amount and captured-status verification remain in place. Configure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env`; no live credentials are included.
- Added migration `0006_walkin_payments_optional_phone`. Existing records are preserved; `Payment.member` is now nullable solely to support payments not attached to a membership.

### Upgrade notes
Run `python manage.py migrate` after extracting this version. Keep your `.env` and database backup. This is packaged as a separate version folder; it does not overwrite V1/V2/V2.1. Partial-payment allocation against a member's outstanding balance and Razorpay webhook reconciliation are not included in this update and should be designed/tested separately before production.


## V4.0 Cashfree update

This package includes the V4.0 Cashfree hosted checkout implementation for online membership registration and renewal. Follow `V4.0_STATUS.md` for Sandbox setup, webhook requirements, and production checks. Cashfree payment activation is performed only after server-side payment verification.

The V4.0 implementation has not been verified against your Cashfree merchant account. Complete Sandbox tests before enabling live payments.


## Refund requests (V4.0 update)
- Members can request a refund against an eligible Cashfree online payment from Payment history.
- Requests are limited to seven calendar days from the recorded payment date and require a reason.
- Owners review requests under Dashboard > Refund requests. Approval submits the refund to Cashfree; rejection does not contact the gateway.
- Refund status can be refreshed from Cashfree. The original payment is marked Refunded only after Cashfree reports SUCCESS.
- Automated refunds are for Cashfree gateway payments only. Offline payments must be handled directly by the gym.
- Refund processing requires valid Cashfree credentials and an order that Cashfree permits to be refunded. Test in Sandbox before production.

## Important setup and security
- Copy .env.example to .env and enter your current Sandbox credentials locally. Never share .env or commit it.
- This package intentionally excludes .env; the existing database file is retained as supplied.
- After updating, run python manage.py migrate to create the refund-request table.
- The Cashfree credentials previously shared in chat should be regenerated before using this package.
