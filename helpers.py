import csv
import datetime
import re
import urllib
import uuid
from functools import wraps

import pytz
import requests
from flask import redirect, render_template, session


def apology(msg: str, code: int = 400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return (
        render_template("apology.html", top=code, bottom=escape(msg)),
        code,
    )


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol: str) -> dict:
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"User-Agent": "python-requests", "Accept": "*/*"},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(
            csv.DictReader(response.content.decode("utf-8").splitlines())
        )
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {"name": symbol, "price": price, "symbol": symbol}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return {}


def usd(value: float) -> str:
    """Format value as USD."""
    return f"${value:,.2f}"


def is_strong_password(password: str) -> str:
    """Verify the strength of 'password'.
    Returns a string indicating the wrong criteria.

    A password is considered strong if:
        8 characters length or more
        1 digit or more
        1 symbol or more
        1 uppercase letter or more
        1 lowercase letter or more
    """

    criteria = [
        (len(password) >= 8, "Password must be at least 8 characters long."), 
        (re.search(r"\d", password), "Password must contain at least one digit."),
        (re.search(r"[A-Z]", password), "Password must contain at least one uppercase letter."),
        (re.search(r"[a-z]", password), "Password must contain at least one lowercase letter."),
        (re.search(r"\W", password), "Password must contain at least one special character"),
    ]

    for cond, msg in criteria:
        if not cond:
            return msg

    return "Success."


