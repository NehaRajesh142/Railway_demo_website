import sqlite3
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "railway-demo-secret-key"
DB = "railway.db"

MAX_PASSENGERS_PER_BOOKING = 6
MAX_ADVANCE_BOOKING_DAYS = 120
MIN_AGE = 0
MAX_AGE = 120


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_number TEXT NOT NULL,
            train_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            class TEXT NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            fare INTEGER NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnr TEXT UNIQUE NOT NULL,
            train_id INTEGER NOT NULL,
            journey_date TEXT NOT NULL,
            passenger_name TEXT NOT NULL,
            passenger_count INTEGER NOT NULL,
            passengers TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (train_id) REFERENCES trains (id)
        )
    """)
    conn.commit()

    # Seed sample trains only once
    c.execute("SELECT COUNT(*) FROM trains")
    if c.fetchone()[0] == 0:
        sample_trains = [
            ("12639", "Brindavan Express", "Chennai", "Bangalore", "07:50", "13:15", "AC", 4, 4, 850),
            ("12639", "Brindavan Express", "Chennai", "Bangalore", "07:50", "13:15", "Sleeper", 3, 3, 350),
            ("12007", "Shatabdi Express", "Chennai", "Bangalore", "06:00", "10:30", "AC", 2, 2, 1200),
            ("16022", "Kaveri Express", "Chennai", "Bangalore", "21:30", "05:45", "Sleeper", 5, 5, 320),
            ("12621", "Tamil Nadu Express", "Chennai", "Delhi", "22:00", "20:30", "AC", 3, 3, 2400),
            ("12621", "Tamil Nadu Express", "Chennai", "Delhi", "22:00", "20:30", "Sleeper", 4, 4, 900),
            ("12163", "Chennai Mail", "Chennai", "Coimbatore", "20:15", "05:30", "Sleeper", 0, 0, 400),
            ("12163", "Chennai Mail", "Chennai", "Coimbatore", "20:15", "05:30", "General", 6, 2, 150),
        ]
        c.executemany("""
            INSERT INTO trains (train_number, train_name, source, destination,
                                 departure_time, arrival_time, class,
                                 total_seats, available_seats, fare)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_trains)
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Validation helpers (each maps to a test case from the test plan)
# ---------------------------------------------------------------------------
def validate_search(source, destination, journey_date):
    """Returns (is_valid, error_message)"""
    if not source or not destination or not journey_date:
        return False, "All search fields are required."

    if source.strip().lower() == destination.strip().lower():
        return False, "Source and destination cannot be the same."

    try:
        date_obj = datetime.strptime(journey_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format."

    today = datetime.now().date()
    if date_obj < today:
        return False, "Journey date cannot be in the past."

    if date_obj > today + timedelta(days=MAX_ADVANCE_BOOKING_DAYS):
        return False, f"Bookings open only {MAX_ADVANCE_BOOKING_DAYS} days in advance."

    return True, None


def validate_booking(passenger_count, passengers):
    """passengers: list of dicts with 'name' and 'age'"""
    if passenger_count < 1:
        return False, "At least one passenger is required."

    if passenger_count > MAX_PASSENGERS_PER_BOOKING:
        return False, f"Maximum {MAX_PASSENGERS_PER_BOOKING} passengers allowed per booking."

    for p in passengers:
        if not p.get("name", "").strip():
            return False, "Passenger name cannot be empty."
        try:
            age = int(p.get("age"))
        except (TypeError, ValueError):
            return False, f"Invalid age for passenger '{p.get('name')}'."
        if age < MIN_AGE or age > MAX_AGE:
            return False, f"Age must be between {MIN_AGE} and {MAX_AGE} for passenger '{p.get('name')}'."

    return True, None


def generate_pnr():
    return "".join(random.choices(string.digits, k=10))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db()
    stations = conn.execute(
        "SELECT DISTINCT source FROM trains UNION SELECT DISTINCT destination FROM trains"
    ).fetchall()
    conn.close()
    station_list = sorted(set(row[0] for row in stations))
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", stations=station_list, today=today)


@app.route("/search", methods=["POST"])
def search():
    source = request.form.get("source", "")
    destination = request.form.get("destination", "")
    journey_date = request.form.get("journey_date", "")

    is_valid, error = validate_search(source, destination, journey_date)
    if not is_valid:
        flash(error, "error")
        return redirect(url_for("index"))

    conn = get_db()
    trains = conn.execute("""
        SELECT * FROM trains WHERE LOWER(source) = LOWER(?) AND LOWER(destination) = LOWER(?)
    """, (source.strip(), destination.strip())).fetchall()
    conn.close()

    return render_template("search_results.html", trains=trains, source=source,
                            destination=destination, journey_date=journey_date)


@app.route("/book/<int:train_id>/<journey_date>", methods=["GET", "POST"])
def book(train_id, journey_date):
    conn = get_db()
    train = conn.execute("SELECT * FROM trains WHERE id = ?", (train_id,)).fetchone()

    if train is None:
        conn.close()
        flash("Train not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        passenger_count = int(request.form.get("passenger_count", 0))
        names = request.form.getlist("passenger_name[]")
        ages = request.form.getlist("passenger_age[]")
        genders = request.form.getlist("passenger_gender[]")
        payment_outcome = request.form.get("payment_outcome", "success")

        passengers = [{"name": n, "age": a, "gender": g} for n, a, g in zip(names, ages, genders)]

        is_valid, error = validate_booking(passenger_count, passengers)
        if not is_valid:
            conn.close()
            flash(error, "error")
            return redirect(url_for("book", train_id=train_id, journey_date=journey_date))

        # Simulate payment gateway
        if payment_outcome == "fail":
            conn.close()
            flash("Payment failed. Booking not confirmed. Seats not deducted.", "error")
            return redirect(url_for("book", train_id=train_id, journey_date=journey_date))

        # Determine confirmed vs waitlisted
        status = "Confirmed" if train["available_seats"] >= passenger_count else "Waitlisted"

        pnr = generate_pnr()
        passengers_str = "; ".join(f"{p['name']} ({p['age']}/{p['gender']})" for p in passengers)

        conn.execute("""
            INSERT INTO bookings (pnr, train_id, journey_date, passenger_name,
                                   passenger_count, passengers, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pnr, train_id, journey_date, passengers[0]["name"], passenger_count,
              passengers_str, status, datetime.now().isoformat()))

        if status == "Confirmed":
            conn.execute("UPDATE trains SET available_seats = available_seats - ? WHERE id = ?",
                         (passenger_count, train_id))

        conn.commit()
        conn.close()
        return redirect(url_for("confirmation", pnr=pnr))

    conn.close()
    return render_template("book.html", train=train, journey_date=journey_date,
                            max_passengers=MAX_PASSENGERS_PER_BOOKING)


@app.route("/confirmation/<pnr>")
def confirmation(pnr):
    conn = get_db()
    booking = conn.execute("""
        SELECT bookings.*, trains.train_name, trains.train_number, trains.source,
               trains.destination, trains.class, trains.fare
        FROM bookings JOIN trains ON bookings.train_id = trains.id
        WHERE pnr = ?
    """, (pnr,)).fetchone()
    conn.close()

    if booking is None:
        flash("Booking not found.", "error")
        return redirect(url_for("index"))

    return render_template("confirmation.html", booking=booking)


@app.route("/my-bookings")
def my_bookings():
    conn = get_db()
    bookings = conn.execute("""
        SELECT bookings.*, trains.train_name, trains.train_number, trains.source,
               trains.destination, trains.class
        FROM bookings JOIN trains ON bookings.train_id = trains.id
        ORDER BY bookings.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("my_bookings.html", bookings=bookings)


@app.route("/cancel/<pnr>", methods=["POST"])
def cancel(pnr):
    conn = get_db()
    booking = conn.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,)).fetchone()

    if booking is None:
        conn.close()
        flash("Booking not found.", "error")
        return redirect(url_for("my_bookings"))

    if booking["status"] == "Cancelled":
        conn.close()
        flash("Booking already cancelled.", "error")
        return redirect(url_for("my_bookings"))

    if booking["status"] == "Confirmed":
        conn.execute("UPDATE trains SET available_seats = available_seats + ? WHERE id = ?",
                     (booking["passenger_count"], booking["train_id"]))

    conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE pnr = ?", (pnr,))
    conn.commit()
    conn.close()

    flash(f"Booking {pnr} cancelled. Refund initiated for confirmed seats.", "success")
    return redirect(url_for("my_bookings"))


@app.route("/reset-demo-data")
def reset_demo_data():
    """Utility route to reset the DB to its seeded state (handy between test runs)."""
    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS trains")
    conn.execute("DROP TABLE IF EXISTS bookings")
    conn.commit()
    conn.close()
    init_db()
    flash("Demo data has been reset.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
