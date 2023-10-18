import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import (apology, is_strong_password, login_required, lookup,
                     need_whole_number, usd)

# Configure application
app = Flask(__name__)
limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
)


# Custom filter
app.jinja_env.filters["usd"] = usd

db = None


def configure_app(app):
    """
    Configure the Flask application with session and database settings.

    Sets up Flask application to use filesystem-based sessions (instead
    of signed cookies) andconfigures the CS50 library to use a SQLite
    database.
    """
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.debug = True
    Session(app)

    # Configure CS50 Library to use SQLite database
    global db
    db = SQL("sqlite:///finance.db")


@app.errorhandler(429)
def ratelimit_handler(e):
    return apology("Rate limit exceeded.", 429)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks."""

    # Query to retrieve distinct stock symbols and the sum of shares owned
    # for each stock
    stocks = db.execute(
        """
        SELECT symbol, SUM(shares) AS shares
        FROM transactions 
        WHERE user_id = ? AND symbol IS NOT NULL AND symbol != ''
        GROUP BY symbol
        """,
        session["user_id"],
    )

    total_shares_worth = 0

    # Calculate total shares' worth and collect stock prices
    for stock in stocks:
        # Lookup stock price
        stock_info = lookup(stock["symbol"])

        if stock_info:
            stock_price = stock_info["price"]
            shares = stock["shares"]
            total_shares_worth += stock_price * shares
            stock.update({"price": stock_price, "total": stock_price * shares})

    cash = retrieve_cash()

    return render_template(
        "index.html",
        stocks=stocks,
        cash=cash,
        grand_total=cash + total_shares_worth,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "GET":
        return render_template("buy.html")

    symbol = request.form.get("symbol")
    shares = request.form.get("shares")

    if not symbol or not shares:
        return apology("Please fill in all the fields.")

    # Check if the symbol exists
    stock_info = lookup(symbol)

    if not stock_info:
        return apology("The symbol does not exist.")

    try:
        shares = need_whole_number(shares)
    except FractionalSharesError:
        return apology("Shares must be a whole number.")

    if shares < 1:
        return apology("The number of shares can not be less than 1.")

    # Calculate the total cost of the shares
    cost = shares * stock_info["price"]

    # Check if the user can afford the shares
    cash = retrieve_cash()

    if cash < cost:
        return apology("Insufficient balance.", 403)

    update_cash(cash - cost)
    record_transaction(stock_info, shares, "buy")
    flash("Bought!")
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    transactions = db.execute(
        """
        SELECT symbol, shares, price, datetime(date, 'unixepoch') AS date
        FROM transactions
        WHERE user_id = ?
        """,
        session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("100/day;10/hour", override_defaults=True)
def login():
    """Log user in."""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    # Ensure username and password were submitted
    if not password:
        return apology("Please fill all the fields.", 403)

    # Query database for username
    rows = db.execute(
        """
        SELECT * 
        FROM users 
        WHERE username = ?
        """,
        username,
    )

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        return apology("Invalid username and/or password", 403)

    # Remember which user has logged in
    session["user_id"] = rows[0]["id"]

    # Redirect user to home page
    return redirect("/")


@app.route("/logout")
def logout():
    """Log user out."""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    symbol = request.form.get("symbol")

    if not symbol:
        return apology("Please fill all the fields.")

    stock_info = lookup(symbol)

    if stock_info:
        return render_template(
            "quoted.html",
            price=stock_info["price"],
            name=stock_info["name"],
            symbol=stock_info["symbol"],
        )
    return apology("Symbol does not exist.")


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("50/day;5/hour", override_defaults=True)
def register():
    """Register user."""
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    users = db.execute(
        """
        SELECT * 
        FROM users 
        WHERE username = ?
        """,
        username,
    )

    if not username or not password or not confirmation:
        return apology("Please fill in all fields.")

    if users:
        return apology("Username already exists.")

    res = is_strong_password(password)

    if res != "Success.":
        return apology(res)

    if password != confirmation:
        return apology("Passwords do not match.", 403)

    db.execute(
        """
        INSERT INTO users (username, hash) 
        VALUES(?, ?)
        """,
        username,
        generate_password_hash(password),
    )
    flash("Registered!")
    return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "GET":
        stocks = db.execute(
            """
            SELECT symbol 
            FROM transactions 
            WHERE user_id = ? 
            GROUP BY symbol 
            HAVING SUM(shares) > 0
            """,
            session["user_id"],
        )
        return render_template("sell.html", stocks=stocks)

    symbol = request.form.get("symbol")
    shares = request.form.get("shares")

    if not symbol or not shares:
        return apology("Please input all the fields.")

    try:
        shares = need_whole_number(shares)
    except FractionalSharesError:
        return apology("Shares must be a whole number.")

    # Check if the user owns the stock
    cur_shares = db.execute(
        """
        SELECT SUM(shares) AS total 
        FROM transactions 
        WHERE user_id = ? AND symbol = ?
        """,
        session["user_id"],
        symbol,
    )
 
    total_shares = cur_shares[0]["total"] if cur_shares else 0

    if total_shares < shares:
        return apology("You don't own enough shares of this stock.")

    if shares < 0:
        return apology("You can't sell negative shares.")

    # Update user's cash balance
    stock_info = lookup(symbol)
    profit = shares * stock_info["price"]
    update_cash(retrieve_cash() + profit)

    record_transaction(stock_info, -shares, "sold")
    flash("Sold!")
    return redirect("/")


def retrieve_cash() -> list:
    return db.execute(
        """
                SELECT cash 
                FROM users 
                WHERE id = ?
                """,
        session["user_id"],
    )[0]["cash"]


def update_cash(amount: int) -> list:
    return db.execute(
        """
                UPDATE users
                SET cash = ? 
                WHERE id = ?
                """,
        amount,
        session["user_id"],
    )


def record_transaction(stock_info: dict, shares: int, trans_type: str) -> None:
    # Store the UTC timestamp in the database to ensure consistency across
    # time zones.
    db.execute(
        """
            INSERT INTO transactions(user_id, symbol, shares, price, date, type)
            VALUES(?, ?, ?, ?, UNIXEPOCH(), ?)
            """,
        session["user_id"],
        stock_info["name"],
        shares,
        stock_info["price"],
        trans_type,
    )


if __name__ == "__main__":
    configure_app(app)
    app.run()
