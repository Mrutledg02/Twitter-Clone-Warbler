"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        
        # Drop all tables to ensure a clean state
        db.drop_all()
        # Recreate all tables
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        user1 = User.signup("testuser1", "test1@test.com", "password", None)
        user2 = User.signup("testuser2", "test2@test.com", "password", None)

        db.session.commit()

        self.user1 = user1
        self.user2 = user2

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_repr(self):
        """Does the repr method work as expected?"""
        self.assertEqual(repr(self.user1), "<User #1: testuser1, test1@test.com>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))

    def test_is_not_following(self):
        """Does is_following successfully detect when user1 is not following user2?"""
        self.assertFalse(self.user1.is_following(self.user2))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        self.user2.following.append(self.user1)
        db.session.commit()
        self.assertTrue(self.user1.is_followed_by(self.user2))

    def test_is_not_followed_by(self):
        """Does is_followed_by successfully detect when user1 is not followed by user2?"""
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_signup(self):
        """Does User-create successfully create a new user given valid credentials?"""
        new_user = User.signup("newuser", "newuser@test.com", "password", None)
        db.session.commit()
        self.assertIsNotNone(new_user)

    def test_signup_fail(self):
        """Does User-create fail to create a new user if any of the validations fail?"""
        with self.assertRaises(ValueError):
            User.signup(None, "test@test.com", "password", None)
            db.session.commit()

    def test_authenticate_valid(self):
        """Does User.authenticate successfully return a user when given valid credentials?"""
        user = User.authenticate("testuser1", "password")
        self.assertEqual(user, self.user1)

    def test_authenticate_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        user = User.authenticate("invalidusername", "password")
        self.assertFalse(user)

    def test_authenticate_invalid_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""
        user = User.authenticate("testuser1", "invalidpassword")
        self.assertFalse(user)