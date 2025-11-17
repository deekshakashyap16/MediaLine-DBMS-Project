import mysql.connector
from flask import Flask, render_template, g, redirect, url_for, request, session, flash
from mysql.connector import pooling
from functools import wraps
from flask import session, flash, redirect, url_for
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_strong_secret_key'

db_config = {
    'user': 'root',
    'password': 'root',   # replace with your real password
    'host': '127.0.0.1',
    'database': 'media_line'
}

# Create a global connection pool (auto-manages open/closed connections)
cnxpool = pooling.MySQLConnectionPool(pool_name="media_pool",
                                      pool_size=5,
                                      pool_reset_session=True,
                                      **db_config)


def get_db():
    """Get a database connection from the pool. Ensures valid connection."""
    if 'db' not in g or not g.db.is_connected():
        g.db = cnxpool.get_connection()
    return g.db

def query_db(query, args=(), one=False):
    """Executes SELECT or other read queries safely."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(query, args)
        rv = cursor.fetchall()
        db.commit()
        return (rv[0] if rv else None) if one else rv
    except mysql.connector.Error as err:
        print(f"[SQL Error] {err} | Query: {query}")
        db.rollback()
        return []
    finally:
        cursor.close()

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db and db.is_connected():
        db.close()


# Routes
@app.route('/')
@login_required
def home():
    popular = query_db("SELECT * FROM vw_popular_content")
    all_content = query_db("SELECT * FROM content")
    users = query_db("SELECT User_ID, Name FROM user")
    return render_template('home.html', popular=popular, all_content=all_content, users=users)

@app.route('/movies')
@login_required
def movies():
    data = query_db("SELECT * FROM content WHERE Type='Movie'")
    return render_template('movies.html', movies=data)

@app.route('/series')
@login_required
def series():
    data = query_db("SELECT * FROM content WHERE Type='Series'")
    return render_template('series.html', series=data)

@app.route('/users')
@login_required
def users():
    data = query_db("SELECT * FROM user")
    return render_template('users.html', users=data)

@app.route("/database_objects")
def database_objects():
    db = get_db()  # ✅ use your existing get_db() helper
    cursor = db.cursor(dictionary=True)

    # Fetch all database objects
    cursor.execute("SHOW FULL TABLES IN media_line WHERE TABLE_TYPE LIKE 'VIEW';")
    views = cursor.fetchall()

    cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'media_line';")
    procedures = cursor.fetchall()

    cursor.execute("SHOW FUNCTION STATUS WHERE Db = 'media_line';")
    functions = cursor.fetchall()

    cursor.execute("SHOW TRIGGERS;")
    triggers = cursor.fetchall()

    cursor.close()

    return render_template(
        "database_objects.html",
        views=views,
        procedures=procedures,
        functions=functions,
        triggers=triggers
    )


@app.route('/content/<int:media_id>')
@login_required
def content_details(media_id):
    """Shows detailed information about a piece of content."""
    content = query_db("SELECT * FROM content WHERE Media_ID = %s", (media_id,), one=True)
    if not content:
        return redirect(url_for('home'))

    # Get details based on type
    if content['Type'] == 'Movie':
        details = query_db("SELECT Total_duration FROM movie WHERE Media_ID = %s", (media_id,), one=True)
    elif content['Type'] == 'Series':
        details = query_db("SELECT num_of_seasons, num_of_episodes FROM series WHERE Media_ID = %s", (media_id,), one=True)
    else:
        details = None  # For other content types

    # Get genres and team
    genres = query_db("SELECT Genre_name FROM genre WHERE Media_ID = %s", (media_id,))
    team = query_db("SELECT Member_name, Role FROM team WHERE Media_ID = %s", (media_id,))

    return render_template(
        'content_details.html',
        content=content,
        details=details,
        genres=genres,
        team=team
    )

def call_procedure(proc_name, args=()):
    try:
        conn = cnxpool.get_connection()
        cur = conn.cursor(dictionary=True)

        # Execute the procedure
        cur.callproc(proc_name, args)

        # Necessary for INSERT/UPDATE in stored procedures
        conn.commit()

        # Capture result sets
        results = []
        for result in cur.stored_results():
            results = result.fetchall()

        cur.close()
        conn.close()
        return results

    except mysql.connector.Error as err:
        print(f"[PROC ERROR {proc_name}] {err}")
        return []


@app.route('/user/<int:user_id>')
def user_history(user_id):
    user = query_db("SELECT * FROM user WHERE User_ID = %s", (user_id,), one=True)
    if not user:
        return redirect(url_for('users'))

    # Use separate connection for procedure
    history = call_procedure("sp_watch_history", (user_id,))

    # Normal query uses pool connection
    total_time = query_db("SELECT fn_total_watch_time(%s) AS total_time", (user_id,), one=True)
    total_seconds = total_time['total_time'] if total_time else 0

    return render_template("user_history.html",
                           user=user,
                           history=history,
                           total_seconds=total_seconds)

from datetime import date
from flask import request, flash, redirect, url_for, render_template

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]  # ✅ no hashing — store plain text
        name = request.form["name"]
        dob = "2000-01-01"  # optional: add a real input later
        address = "N/A"
        email = request.form["email"]
        card = "N/A"
        phone = "N/A"
        start_date = date.today()

        try:
            conn = get_db()
            cursor = conn.cursor()

            # ✅ Match exact parameter order of sp_add_user
            cursor.callproc("sp_add_user", (
                username, password, name, dob, address, email, card, phone, start_date
            ))

            conn.commit()
            cursor.close()

            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            print(f"[Signup Error] {e}")
            flash("Signup failed. Try again.", "danger")

    return render_template("signup.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs in an existing user."""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = query_db("SELECT * FROM user WHERE Email = %s", (email,), one=True)

        if user and user["Password"] == password:
            session["user_id"] = user["User_ID"]
            session["user_name"] = user["Name"]
            flash(f"Welcome, {user['Name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")
@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    user = query_db("SELECT * FROM user WHERE User_ID = %s", (user_id,), one=True)
    history = call_procedure("sp_watch_history", (user_id,))
    total_time = query_db("SELECT fn_total_watch_time(%s) AS total_time", (user_id,), one=True)
    likes = query_db("SELECT * FROM vw_user_likes WHERE User_ID = %s", (user_id,))
    return render_template("profile.html", user=user, history=history, total_time=total_time["total_time"], likes=likes)


@app.route("/logout")
def logout():
    """Logs out the current user."""
    session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Personalized user dashboard."""
    if "user_id" not in session:
        flash("Please log in to view your dashboard.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = query_db("SELECT * FROM user WHERE User_ID = %s", (user_id,), one=True)
    history = call_procedure("sp_watch_history", (user_id,))
    total_time = query_db("SELECT fn_total_watch_time(%s) AS total_time", (user_id,), one=True)
    liked_content = query_db("""
    SELECT c.Name, c.Type
    FROM liked l
    JOIN content c ON l.Media_ID = c.Media_ID
    WHERE l.User_ID = %s
""", (user_id,))


    return render_template(
        "dashboard.html",
        user=user,
        history=history,
        total_time=total_time["total_time"] if total_time else 0,
        liked_content=liked_content
    )

@app.route('/watch/<int:media_id>')
@login_required
def watch_content(media_id):
    user_id = session["user_id"]

    # add 100 seconds each click
    call_procedure("sp_watch_now", (user_id, media_id, 100))

    flash("Watch recorded! +100 seconds added.", "success")
    return redirect(url_for('content_details', media_id=media_id))


@app.route('/like/<int:media_id>', methods=['POST', 'GET'])
@login_required
def like_content(media_id):
    """Likes content for the logged-in user using stored procedure sp_like_content."""
    if 'user_id' not in session:
        flash("Please log in to like content.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.callproc('sp_like_content', (user_id, media_id))
        conn.commit()
        cursor.close()
        flash("Content added to your liked list!", "success")
    except Exception as e:
        print(f"[LIKE ERROR] {e}")
        flash("You have already liked this content.", "info")

    return redirect(url_for('content_details', media_id=media_id))


if __name__ == '__main__':
    app.run(debug=True)
