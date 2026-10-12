# RailBook Demo — Railway Reservation Testing Project

A small Flask app that simulates ticket **search** and **booking** so it can be
used as the System Under Test (SUT) for a software testing mini project.

## Setup

```bash
cd railway_demo
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser. A SQLite file `railway.db`
is created automatically and seeded with sample trains and routes.

To wipe bookings and reset seat counts during testing, visit `/reset-demo-data`
or click "Reset Data" in the nav bar.

## Seeded Routes (for test design)

| Route | Class | Seats | Notes |
|---|---|---|---|
| Chennai → Bangalore | AC / Sleeper | 4 / 3 | Normal booking flow |
| Chennai → Bangalore | AC (Shatabdi) | 2 | Low-seat edge case |
| Chennai → Delhi | AC / Sleeper | 3 / 4 | Long route |
| Chennai → Coimbatore | Sleeper | **0** | Fully booked → tests waitlist |
| Chennai → Coimbatore | General | 2 of 6 | Partial availability |

## Validation Rules Implemented (maps to earlier test cases)

**Search validation** (`validate_search` in `app.py`):
- Source and destination required, and cannot be identical (TC02)
- Journey date must be a valid date, not in the past (TC03)
- Journey date cannot be more than 120 days ahead
- No matching trains → "No trains found" message (TC04)

**Booking validation** (`validate_booking` in `app.py`):
- Passenger count must be between 1 and 6 (TC06)
- Passenger name required
- Passenger age must be a number between 0 and 120 (TC07)
- Simulated payment can be forced to succeed or fail via a dropdown on the
  booking form (TC09) — booking is only confirmed and seats only deducted on
  success
- If requested seats exceed availability, booking is auto-**waitlisted**
  instead of confirmed (TC08)
- PNR (10-digit) generated only on successful booking (TC05)
- Cancelling a confirmed booking releases the seat back into availability
  (TC10)

## Suggested Manual Test Pass

Use the test case table from the test plan (TC01–TC10) and execute each
against this app, recording Actual Result and Pass/Fail. Because the payment
outcome and seat counts are easy to control here, this app is also a good
target for a first Selenium script (e.g. automate TC01, TC05, TC06, TC09).

## Project Structure

```
railway_demo/
├── app.py                  # Flask routes + validation logic
├── requirements.txt
├── railway.db               # created on first run
├── templates/
│   ├── base.html
│   ├── index.html            # search form
│   ├── search_results.html
│   ├── book.html             # passenger + payment form
│   ├── confirmation.html     # PNR / ticket summary
│   └── my_bookings.html      # list + cancel
└── static/
    └── style.css
```
