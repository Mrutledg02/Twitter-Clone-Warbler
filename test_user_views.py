# When writing tests, it's important to test both the expected behavior and edge cases. For example, what happens when a user tries to like their own message?

"""User Views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py

from unittest import TestCase
from app import app, db, User, Message, CURR_USER_KEY  # Import CURR_USER_KEY from app.py

# Make sure to use a different database for testing
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler-tet"

# Disable CSRF protection in Flask-WTF forms during testing
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors real errors instead of HTML pages with error info
app.config['TESTING'] = True

class UserViewsTestCase(TestCase):
    """Test views for user-related routes."""

    def setUp(self):
        """Clean up any existing user data and create a test client."""
        db.drop_all()
        db.create_all()

        # Create a test user
        self.user = User.signup("testuser", "test@test.com", "password", None)
        db.session.add(self.user)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transactions."""
        db.session.rollback()

    def test_signup(self):
        """Test user signup."""
        with self.client as c:
            # Send a POST request to the signup route
            response = c.post('/signup', data={"username": "newuser", "email": "new@test.com", "password": "newpassword"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            # Check if the user is redirected to the homepage after signup
            self.assertIn(b"Welcome to Warbler", response.data)

    def test_login(self):
        """Test user login."""
        with self.client as c:
            # Send a POST request to the login route
            response = c.post('/login', data={"username": "testuser", "password": "password"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            # Check if the user is redirected to the homepage after login
            self.assertIn(b"Hello, testuser!", response.data)

    def test_following_page_logged_in(self):
        """Test accessing the following page when logged in."""
        with self.client as c:
            # Log in as the test user
            c.post('/login', data={"username": "testuser", "password": "password"}, follow_redirects=True)
            # Access the following page of the test user
            response = c.get(f'/users/{self.user.id}/following')
            # Check if the response status code is 200
            self.assertEqual(response.status_code, 200)

    def test_followers_page_logged_in(self):
        """Test accessing the followers page of another user when logged in."""
        with self.client as c:
            # Log in as the test user
            c.post('/login', data={"username": "testuser", "password": "password"}, follow_redirects=True)
            
            # Create another user for testing
            other_user = User.signup("otheruser", "other@test.com", "password", None)
            db.session.add(other_user)
            db.session.commit()

            # Access the followers page of the other user
            response = c.get(f'/users/{other_user.id}/followers')
            
            # Check if the response status code is 200
            self.assertEqual(response.status_code, 200)

    def test_following_page_logged_out(self):
        """Test disallowing access to the following page when logged out."""
        with self.client as c:
            # Access the following page of the test user without logging in
            response = c.get(f'/users/{self.user.id}/following', follow_redirects=True)
            # Check if the user is redirected to the home page
            self.assertIn(b"Access unauthorized", response.data)
            self.assertNotIn(b"Login", response.data)

    def test_follower_page_logged_out(self):
        """Test disallowing access to the follower page when logged out."""
        with self.client as c:
            # Access the follower page of the test user without logging in
            response = c.get(f'/users/{self.user.id}/followers', follow_redirects=True)
            # Check if the user is redirected to the home page
            self.assertIn(b"Access unauthorized", response.data)
            self.assertNotIn(b"Login", response.data)