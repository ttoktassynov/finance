import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#Add secret key
app.config['SECRET_KEY'] = 'f9bf78b9a18ce6d46a0cd2b0b86df9da'

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use Postres database
#db = SQL(os.getenv("DATABASE_URL"))
db = SQL("sqlite:///finance.db")
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/.well-known/acme-challenge/XBv8CK7dwG4QBag-xKaOLk51EbElzAmdhO3qblA9Eeo")
def well_known():
    return "XBv8CK7dwG4QBag-xKaOLk51EbElzAmdhO3qblA9Eeo.BOM2A_2wYrYgHD8PpC9djr8E-gEZLwPgL5P4OYLKcKg"

@app.route("/")
@login_required
def index():
    #st
    rows = []
    uid = session["user_id"]
    query = "SELECT symbol, sum(shares) as shares FROM transactions group by user_id, symbol having user_id = :uid and sum(shares) >0"
    sums = db.execute(query, uid=uid)
    grand = 0
    cashrow = db.execute("SELECT cash FROM users WHERE id = :uid", uid=uid)
    cash = float(cashrow[0]["cash"])
    for s in sums:
        row = {}
        row["symbol"] = s["symbol"]
        result = lookup(row["symbol"])
        if not result:
            return apology("Bad symbol in database")
        row["price"] = usd(result["price"])
        row["name"] = result["name"]
        row["shares"] = s["shares"]
        total = float(result["price"]) * int(s["shares"])
        grand = grand + total
        row["total"] = usd(total)
        rows.append(row)
    grand = usd(grand + cash)
    return render_template("index.html", rows=rows, cash=usd(cash), grand=grand)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        sym = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        if not shares:
            return apology("Missing shares")
        res = lookup(sym)
        if not res:
            return apology("Invalid symbol")
        price = float(res["price"])
        uid = session["user_id"]
        rows = db.execute("SELECT cash FROM users WHERE id = :uid", uid = uid)
        cash = float(rows[0]["cash"])
        if price * shares > cash:
            return apology("can't afford it")

        db.execute("INSERT INTO transactions (symbol, user_id, shares, price) values (:sym, :uid, :sh, :pr)",
            sym=sym, uid=uid, sh=shares, pr=price)

        left = cash - price * shares
        db.execute("UPDATE users SET cash = :cash WHERE id = :uid",
            cash=left, uid=uid)

        flash("You successfully bought shares!")
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    uid = session["user_id"]
    rows = db.execute("SELECT symbol, shares, price, date FROM transactions where user_id = :uid order by date",
        uid = uid)
    return render_template("history.html", rows=rows)

@app.route("/changePass", methods=["GET", "POST"])
@login_required
def changePass():
    """Change password"""
    uid = session["user_id"]
    if (request.method == "GET"):
        return render_template("changePass.html")
    else:
        oldPass = request.form.get("oldPass")
        newPass = request.form.get("newPass")
        newPassConf = request.form.get("newPassConf")
        # Validate inputs
        if not oldPass or not newPass or not newPassConf:
            return apology("Must provide passwords", 403)
        rows = db.execute("SELECT hash FROM users where id=:uid",
            uid=uid)
        if not check_password_hash(rows[0]["hash"], oldPass):
            return apology("Old password incorrect", 403)
        if newPass != newPassConf:
            return apology("New password must match", 403)
        h = generate_password_hash(newPass)
        db.execute("UPDATE users SET hash=:hashVal where id=:uid",
            hashVal = h, uid = uid)
        # Redirect user to home page
        flash("You successfully changed password!")
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("You successfully logged in!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("You successfully logged out!")
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        res = lookup(request.form.get("symbol"))
        if not res:
            return apology("Invalid symbol")
        else:
            flash("You successfully received the quote!")
            return render_template("quoted.html",
            name = res["name"], symbol = res["symbol"], price = usd(res["price"]))



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 403)
        else:
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                username = username)
            if len(rows) == 1:
                return apology("username already exists", 403)

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure password was submitted
        if not password or not confirmation:
            return apology("must provide password", 403)
        elif password != confirmation:
            return apology("passwords must match", 403)

        db.execute("INSERT INTO users (username, hash) values (?, ?)",
            username, generate_password_hash(password))
        flash("You successfully registered!")
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    sym = request.form.get("symbol")
    uid = session["user_id"]

    if request.method == "POST":


        # Check if symbol is set
        if not sym:
            return apology("Symbol not set")

        # Check if user has such shares
        query = "SELECT sum(shares) as shares FROM transactions group by user_id, symbol having user_id = :uid and symbol = :sym and sum(shares) >0"
        rows = db.execute(query, uid=uid, sym=sym)
        if len(rows) != 1:
            return apology("No such symbol in portfolio")

        # Check if shares are not negative and user has enough of them
        shares_got = int(rows[0]["shares"])
        shares = request.form.get("shares")
        if not shares:
            return apology("Enter number of shares")
        shares = int(shares)
        if shares < 0 or shares > shares_got:
            return apology("Wrong shares amount")

        # Get the current price
        q = lookup(sym)
        if not q:
            return apology("Error getting current price")
        price = q["price"]

        # Get current cash amount of user
        urows = db.execute("SELECT cash FROM users where id = :uid", uid=uid)
        cash = float(urows[0]["cash"])

        # Insert into transactions
        db.execute("INSERT INTO transactions (symbol, user_id, shares, price) values (:sym, :uid, :sh, :pr)",
            sym=sym, uid=uid, sh=-shares, pr=price)

        # Update cash of the user
        now = cash + price * shares
        db.execute("UPDATE users SET cash = :cash WHERE id = :uid",
            cash=now, uid=uid)

        flash("You successfully sold shares!")
        return redirect("/")

    else:
        symbols = db.execute("SELECT symbol FROM transactions group by user_id, symbol having user_id = :uid and sum(shares) >0 order by symbol",
            uid = uid)

        return render_template("sell.html", symbols=symbols)
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

def create_app():
   return app

if __name__ == '__main__':
    from waitress import serve
    from decouple import config
    PORT = config('PORT', default=5000, cast=int)
    serve(app, host="0.0.0.0", port=PORT)