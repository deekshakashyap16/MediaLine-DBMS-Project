import mysql.connector
from flask import Flask, render_template, g, redirect, url_for, request, session, flash
from mysql.connector import pooling
from functools import wraps
from flask import session, flash, redirect, url_for
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
import random

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
    'password': 'root',
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
        conn.commit()

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
        username = request.form.get("username")
        password = request.form.get("password")
        name = request.form.get("name")
        dob = request.form.get("dob")
        address = request.form.get("address")
        email = request.form.get("email")
        card = request.form.get("card")
        phone = request.form.get("phone")
        start_date = date.today()

        # Validation
        if not all([username, password, name, dob, address, email, card, phone]):
            flash("All fields are required.", "danger")
            return render_template("signup.html")

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

        except mysql.connector.Error as err:
            print(f"[Signup Error] {err}")
            if "Duplicate entry" in str(err):
                flash("Email or username already exists. Try another.", "danger")
            else:
                flash("Signup failed. Try again.", "danger")
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
            return redirect(url_for("home"))
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
    downloads = query_db("""
        SELECT d.User_ID, d.Media_ID, d.Download_Date, c.Name, c.Type
        FROM download d
        JOIN content c ON d.Media_ID = c.Media_ID
        WHERE d.User_ID = %s
    """, (user_id,))
    return render_template("profile.html", user=user, history=history, total_time=total_time["total_time"], likes=likes, downloads=downloads)


@app.route("/logout")
def logout():
    """Logs out the current user."""
    session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("login"))



@app.route('/watch/<int:media_id>')
@login_required
def watch_content(media_id):
    user_id = session["user_id"]

    # Randomly increment between 50-120 seconds to trigger clipping if needed
    watch_duration = random.randint(50, 120)
    call_procedure("sp_watch_now", (user_id, media_id, watch_duration))

    flash(f"Watch recorded! +{watch_duration} seconds added.", "success")
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


@app.route('/download/<int:media_id>')
@login_required
def download_content(media_id):
    """Downloads content using the download table - triggers default date."""
    user_id = session['user_id']
    content = query_db("SELECT * FROM content WHERE Media_ID = %s", (media_id,), one=True)
    
    if not content:
        flash("Content not found.", "danger")
        return redirect(url_for('home'))
    
    # Check if already downloaded
    existing = query_db("SELECT * FROM download WHERE User_ID = %s AND Media_ID = %s", (user_id, media_id), one=True)
    if existing:
        flash(f"'{content['Name']}' is already in your downloads.", "info")
        return redirect(url_for('content_details', media_id=media_id))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO download (User_ID, Media_ID, Download_Date) VALUES (%s, %s, CURDATE())",
            (user_id, media_id)
        )
        conn.commit()
        cursor.close()
        flash(f"'{content['Name']}' downloaded successfully!", "success")
    except mysql.connector.Error as err:
        flash("Error downloading content.", "danger")
    
    return redirect(url_for('content_details', media_id=media_id))


@app.route('/delete-download/<int:media_id>', methods=['POST'])
@login_required
def delete_download(media_id):
    """Deletes a downloaded content from the user's downloads."""
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM download WHERE User_ID = %s AND Media_ID = %s",
            (user_id, media_id)
        )
        conn.commit()
        cursor.close()
        flash("Download removed from your library.", "success")
    except mysql.connector.Error as err:
        flash("Error deleting download.", "danger")
    
    return redirect(url_for('profile'))


@app.route('/trailers')
@login_required
def trailers():
    """Displays all available trailers using the trailer table."""
    trailers = query_db("""
        SELECT t.Media_ID, c.Name, t.Trailer_name, t.Trailer_duration
        FROM trailer t
        JOIN content c ON t.Media_ID = c.Media_ID
    """)
    return render_template('trailers.html', trailers=trailers)


@app.route('/episodes/<int:media_id>')
@login_required
def view_episodes(media_id):
    """Views episodes of a series using the episode table."""
    series = query_db("SELECT * FROM series WHERE Media_ID = %s", (media_id,), one=True)
    if not series:
        flash("Series not found.", "danger")
        return redirect(url_for('series'))
    
    content = query_db("SELECT * FROM content WHERE Media_ID = %s", (media_id,), one=True)
    episodes = query_db("""
        SELECT Episode_ID, Season_number, Episode_number, Episode_name, Duration, Air_date
        FROM episode
        WHERE Media_ID = %s
        ORDER BY Season_number, Episode_number
    """, (media_id,))
    
    return render_template('episodes.html', content=content, episodes=episodes, series=series)


@app.route('/top-movies')
@login_required
def top_movies():
    """Displays top movies using sp_top_movies stored procedure."""
    top_movies = call_procedure("sp_top_movies", (10,))
    return render_template('top_movies.html', movies=top_movies)


@app.route('/stats')
@login_required
def user_stats():
    """Shows user watch summary statistics using vw_user_watch_summary view."""
    stats = query_db("SELECT * FROM vw_user_watch_summary ORDER BY Total_Duration DESC")
    return render_template('user_stats.html', stats=stats)


@app.route('/watched-status')
@login_required
def watched_status():
    """Shows which content users have watched using fn_has_watched function."""
    user_id = session["user_id"]
    all_content = query_db("SELECT Media_ID, Name, Type FROM content")
    
    watched_list = []
    for content in all_content:
        has_watched = query_db(
            "SELECT fn_has_watched(%s, %s) AS watched", 
            (user_id, content['Media_ID']), 
            one=True
        )
        if has_watched:
            watched_list.append({
                'Media_ID': content['Media_ID'],
                'Name': content['Name'],
                'Type': content['Type'],
                'watched': has_watched.get('watched', 0)
            })
    
    return render_template('watched_status.html', watched=watched_list)


@app.route('/viewers/<int:media_id>')
@login_required
def total_viewers(media_id):
    """Shows total number of viewers for a content using fn_total_viewers function."""
    content = query_db("SELECT * FROM content WHERE Media_ID = %s", (media_id,), one=True)
    
    if not content:
        flash("Content not found.", "danger")
        return redirect(url_for('home'))
    
    viewer_count = query_db(
        "SELECT fn_total_viewers(%s) AS viewer_count", 
        (media_id,), 
        one=True
    )
    viewer_count_val = viewer_count.get('viewer_count', 0) if viewer_count else 0
    
    return render_template('viewers.html', content=content, viewer_count=viewer_count_val)


@app.route('/episode-count/<int:media_id>')
@login_required
def episode_count_page(media_id):
    """Shows episode count for a series using fn_episode_count function."""
    content = query_db("SELECT * FROM content WHERE Media_ID = %s", (media_id,), one=True)
    
    if not content:
        flash("Content not found.", "danger")
        return redirect(url_for('home'))
    
    if content['Type'] != 'Series':
        flash("Episode count is only available for Series.", "info")
        return redirect(url_for('content_details', media_id=media_id))
    
    ep_count = query_db(
        "SELECT fn_episode_count(%s) AS episode_count", 
        (media_id,), 
        one=True
    )
    ep_count_val = ep_count.get('episode_count', 0) if ep_count else 0
    
    return render_template('episode_count.html', content=content, episode_count=ep_count_val)


if __name__ == '__main__':
    app.run(debug=True)
