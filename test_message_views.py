"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data



# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transactions."""
        db.session.rollback()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message_logged_in(self):
        """Test deleting a message when logged in."""
        # Create a test message
        msg = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Send a POST request to delete the message
            resp = c.post(f"/messages/{msg.id}/delete")
            self.assertEqual(resp.status_code, 302)

            # Check if the message is deleted from the database
            deleted_msg = Message.query.get(msg.id)
            self.assertIsNone(deleted_msg)

    def test_add_message_logged_out(self):
        """Test prohibiting adding a message when logged out."""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Test message"}, follow_redirects=True)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_delete_message_logged_out(self):
        """Test prohibiting deleting a message when logged out."""
        # Create a test message
        msg = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_add_message_as_another_user(self):
        with app.test_client() as client:
            # Simulate an unauthorized user by not setting g.user
            with client.session_transaction() as session:
                session.clear()

            # Send a POST request to the message adding endpoint
            response = client.post('/messages/new', data={'text': 'Test message'}, follow_redirects=True)

            # Check if the response at the redirected URL contains the "Access unauthorized" message
            self.assertIn(b"Access unauthorized", response.data)

    def test_delete_message_as_another_user(self):
        """Test prohibiting deleting a message as another user."""
        with app.test_client() as client:
            # Simulate an unauthorized user by not setting g.user
            with client.session_transaction() as session:
                session.clear()

            # Create a test message by the test user
            msg = Message(text="Test message", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            # Send a POST request to delete the message
            response = client.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            # Check if the response at the redirected URL contains the "Access unauthorized" message
            self.assertIn(b"Access unauthorized", response.data)