# RailBook Demo: Railway Reservation Testing Project

A software testing mini project that validates the **ticket search** and **booking** modules of a railway reservation website. RailBook, a small Flask app, is the System Under Test (SUT). Each validation rule in it maps to a documented test case.

## Objectives

- Apply boundary value analysis, equivalence partitioning, functional (black-box), negative and regression testing to a realistic booking flow
- Verify search validation, booking validation, seat-status logic, payment handling and cancellation
- Automate the end-to-end flow in a real browser and capture screenshot evidence

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (auto-created and seeded on first run) |
| Frontend | Jinja2 templates, HTML, CSS, JavaScript |
| Test automation | Flask test client, Playwright (Chromium) |

## Getting Started

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**. The database is created and seeded with sample trains on first run. To restore the original data between test runs, click **Reset Data** in the nav bar or visit `/reset-demo-data`.

## Seeded Test Data

| Route | Class | Seats | Purpose |
|---|---|---|---|
| Chennai → Bangalore | AC / Sleeper | 4 / 3 | Normal booking flow |
| Chennai → Bangalore | AC (Shatabdi) | 2 | Low-seat edge case |
| Chennai → Delhi | AC / Sleeper | 3 / 4 | Long route |
| Chennai → Coimbatore | Sleeper | 0 | Fully booked, tests waitlisting |
| Chennai → Coimbatore | General | 2 of 6 | Partial availability |

## Validation Rules Under Test

**Search**
- Source, destination and date are all required
- Source and destination cannot be the same
- Date must be valid, not in the past, and within 120 days
- A route with no trains shows a "No trains found" message

**Booking**
- 1 to 6 passengers per booking
- Passenger name is required
- Age must be a number between 0 and 120
- Payment outcome can be forced to success or failure via a dropdown; seats are deducted and a PNR is issued only on success
- If requested seats exceed availability, the booking is **Waitlisted** instead of Confirmed
- Cancelling a Confirmed booking releases its seats back to inventory

## Test Cases

| ID | Scenario | Expected Result |
|---|---|---|
| TC01 | Valid search | Matching trains listed |
| TC02 | Source equals destination | Error shown |
| TC03 | Past or invalid date | Error shown |
| TC04 | Route with no trains | "No trains found" message |
| TC05 | Valid booking | Confirmed, 10-digit PNR generated |
| TC06 | 7 passengers | Rejected (max 6) |
| TC07 | Negative or out-of-range age | Rejected |
| TC08 | Seats requested exceed availability | Status set to Waitlisted |
| TC09 | Payment set to Fail | Not confirmed, seat count unchanged |
| TC10 | Cancel a Confirmed booking | Status Cancelled, seats released |

## Browser Automation (optional)

```bash
pip install playwright
playwright install chromium
```

A minimal Playwright run against the live app:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:5000/")
    page.fill("#source", "Chennai")
    page.fill("#destination", "Bangalore")
    page.fill("#journey_date", "2026-12-01")
    page.click("button[type=submit]")
    page.click(".train-card >> text=Book Now")
    page.fill("input[name='passenger_name[]']", "Test User")
    page.fill("input[name='passenger_age[]']", "22")
    page.click("button[type=submit]")
    page.screenshot(path="confirmation.png", full_page=True)
    browser.close()
```

Make sure the journey date is in the future when you run it.

## Project Structure

```
railway_demo/
├── app.py                  # Flask routes and validation logic
├── requirements.txt
├── railway.db              # created on first run
├── templates/
│   ├── base.html
│   ├── index.html          # search form
│   ├── search_results.html
│   ├── book.html           # passenger and payment form
│   ├── confirmation.html   # PNR and ticket summary
│   └── my_bookings.html    # booking list and cancel
└── static/
    └── style.css
```

## Notes

- This is a demo for testing practice, not a real booking system. Payment is simulated.
- `validate_search()` and `validate_booking()` in `app.py` hold the validation rules, so they are the first place to look when a test fails.

## Author

Neha Rajesh, IV CSE-C, Rajalakshmi Institute of Technology
