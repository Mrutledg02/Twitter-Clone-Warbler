# Consider using Flask's url_for function to generate URLs in your templates. This can help avoid hardcoding URLs and make your application easier to maintain.
# It's good practice to handle the case where a database query returns None in your routes. This can happen if an ID does not exist in the database. You can use get_or_404 to simplify this process.

import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.app_context().push()

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# toolbar = DebugToolbarExtension(app)

connect_db(app)

bcrypt = Bcrypt()


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add current user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

            # Flash message upon successful signup
            flash("Welcome to Warbler", "success")

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS
    do_logout()
    flash("You have been successfully logged out.", "success")
    return redirect("/login")

##############################################################################
# Community route:

@app.route('/community')
def community():
    """Show communities page with listing of all users."""

    users = User.query.all()

    return render_template('users/index.html', users=users)

##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized. Please log in.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized. Please log in.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # IMPLEMENT THIS
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        # Check if header image URL is provided, if not, assign default value
        if not form.header_image_url.data:
            form.header_image_url.data = "/static/images/warbler-hero.jpg"

        if g.user.check_password(form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.location = form.location.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data

            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(f"/users/{g.user.id}")
        else:
            flash("Invalid current password. Please try again.", "danger")

    return render_template('users/edit.html', form=form, user_id=g.user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    if g.user:
        followed_users_ids = [user.id for user in g.user.following]
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(followed_users_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        liked_messages = Likes.query.filter_by(user_id=g.user.id).with_entities(Likes.message_id).all()
        liked_message_ids = [int(row[0]) for row in liked_messages]
        for liked_msg_id in liked_message_ids:
            print(type(liked_msg_id))

        return render_template('home.html', messages=messages, liked_message=liked_message_ids)
    else:
        return render_template('home-anon.html')



##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req

##############################################################################
# Like routes

@app.route('/users/add_like/<int:message_id>', methods=['POST'])
def add_like(message_id):
    """Add or remove a like for the currently logged-in user to a message."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")
    
    message = Message.query.get_or_404(message_id)
    
    # Check if the user has already liked the message
    like = Likes.query.filter_by(user_id=g.user.id, message_id=message_id).first()
    
    if like:
        # If the user has already liked the message, remove the like
        db.session.delete(like)
        db.session.commit()
        flash("You've unliked the message.", "warning")
    else:
        # If the user has not liked the message, add a new like
        new_like = Likes(user_id=g.user.id, message_id=message_id)
        db.session.add(new_like)
        db.session.commit()
        flash("You've liked the message.", "success")
    
    return redirect("/")


@app.route('/users/remove_like/<int:message_id>', methods=['POST'])
def remove_like(message_id):
    """Allow the currently logged-in user to unlike a warble."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    message = Message.query.get_or_404(message_id)

    # Check if the user has liked the warble
    like = Likes.query.filter_by(user_id=g.user.id, message_id=message_id).first()
    if not like:
        flash("You haven't liked this warble yet.", "warning")
        return redirect(f"/users/{g.user.id}/likes")  # Redirect to the current user's likes page

    # Remove the like
    db.session.delete(like)
    db.session.commit()

    flash("Warble unliked.", "success")
    return redirect(f"/users/{g.user.id}/likes")  # Redirect to the current user's likes page


@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show messages liked by the user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    user = User.query.get_or_404(user_id)

    # Get the messages liked by the user
    liked_messages = user.likes

    return render_template('users/likes.html', user=user, messages=liked_messages)

##############################################################################
# 404 

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors by rendering the custom 404 page."""
    return render_template('404.html'), 404