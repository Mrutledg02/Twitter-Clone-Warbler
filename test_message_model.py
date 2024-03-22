"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from datetime import datetime
from unittest import TestCase
from models import db, User, Message, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

class MessageModelTestCase(TestCase):
    """Test functions related to Message model."""

    def setUp(self):
        """Create test client, add sample data."""

        # Drop all tables to ensure a clean state
        db.drop_all()
        # Recreate all tables
        db.create_all()

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        user = User.signup("testuser", "test@test.com", "password", None)
        db.session.add(user)
        db.session.commit()

        self.user = user

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_text_attribute(self):
        """Does the text attribute store the message content correctly?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(message.text, "Test message")

    def test_timestamp_attribute(self):
        """Does the timestamp attribute store the message creation time correctly?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()
        self.assertIsInstance(message.timestamp, datetime)

    def test_user_id_attribute(self):
        """Does the user_id attribute correctly associate the message with the user who created it?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()
        self.assertEqual(message.user_id, self.user.id)

    def test_likes_relationship(self):
        """Does the likes relationship correctly associate the message with its likes?"""
        user = User.query.get(1)
        message = Message(
            text="Test message",
            timestamp=datetime.utcnow(),
            user_id=user.id
        )
        db.session.add(message)
        db.session.commit()

        user_like = Likes(user_id=user.id)

        message.likes.append(user_like)  # This line is causing the KeyError

        db.session.commit()

        self.assertIn(user_like, message.likes)

    def test_get_all_messages(self):
        """Does the Message.query.all() method return all messages in the database?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Test message 2", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        messages = Message.query.all()
        self.assertEqual(len(messages), 2)

    def test_get_message_by_id(self):
        """Does the Message.query.get(message_id) method return the correct message by its ID?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        retrieved_message = Message.query.get(message.id)
        self.assertEqual(retrieved_message, message)

    def test_get_messages_by_user_id(self):
        """Does the Message.query.filter_by(user_id=user_id).all() method return all messages associated with a specific user?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Test message 2", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        messages = Message.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(len(messages), 2)

    def test_get_messages_by_user_id_ordered_by_timestamp_desc(self):
        """Does the Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.desc()).all() method return messages associated with a specific user in descending order of timestamp?"""
        message1 = Message(text="Test message 1", user_id=self.user.id, timestamp=datetime.utcnow())
        message2 = Message(text="Test message 2", user_id=self.user.id, timestamp=datetime.utcnow())
        db.session.add_all([message1, message2])
        db.session.commit()

        messages = Message.query.filter_by(user_id=self.user.id).order_by(Message.timestamp.desc()).all()
        self.assertEqual(messages[0], message2)

    def test_search_messages_by_user_and_text(self):
        """Does the Message.query.filter(Message.user_id == user_id, Message.text.ilike('%search_text%')).all() method return messages associated with a specific user containing the search text in their content?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Another test message", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        search_text = "test"
        messages = Message.query.filter(Message.user_id == self.user.id, Message.text.ilike(f'%{search_text}%')).all()
        self.assertEqual(len(messages), 2)
        self.assertIn(message1, messages)
        self.assertIn(message2, messages)

    def test_search_all_messages_by_text(self):
        """Does the Message.query.filter(Message.text.ilike('%search_text%')).all() method return all messages containing the search text in their content?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Another test message", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        search_text = "test"
        messages = Message.query.filter(Message.text.ilike(f'%{search_text}%')).all()
        self.assertEqual(len(messages), 2)

    def test_delete_all_messages(self):
        """Does the Message.query.delete() method delete all messages in the database?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Another test message", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        Message.query.delete()
        db.session.commit()

        messages = Message.query.all()
        self.assertEqual(len(messages), 0)

    def test_delete_messages_by_user_id(self):
        """Does the Message.query.filter_by(user_id=user_id).delete() method delete all messages associated with a specific user?"""
        message1 = Message(text="Test message 1", user_id=self.user.id)
        message2 = Message(text="Another test message", user_id=self.user.id)
        db.session.add_all([message1, message2])
        db.session.commit()

        Message.query.filter_by(user_id=self.user.id).delete()
        db.session.commit()

        messages = Message.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(len(messages), 0)

    def test_add_like_to_message(self):
        """Does the message.likes.append(user) method correctly add a user's like to the message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        user = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.add(user)
        db.session.commit()

        like = Likes(user_id=user.id, message_id=message.id)  # Create a like object
        db.session.add(like)
        db.session.commit()

        # Refresh the message object to reflect the changes made in the database
        db.session.refresh(message)

        # Check if the like object is associated with the message
        self.assertIn(like, message.likes)

    def test_remove_like_from_message(self):
        """Does the message.likes.remove(user) method correctly remove a user's like from the message?"""
        # Create a message
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        # Create a user
        user = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.add(user)
        db.session.commit()

        # Add like to message
        like = Likes(user_id=user.id, message_id=message.id)
        db.session.add(like)
        db.session.commit()

        # Remove like from message
        message.likes.remove(like)
        db.session.commit()

        # Check if like is removed from the message
        self.assertNotIn(like, message.likes)