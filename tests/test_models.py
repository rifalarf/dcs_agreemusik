import unittest
import os
import sys

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(username='john', email='john@example.com')
        u.set_password('cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(username='john', email='john@example.com')
        u.set_password('cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(username='john', email='john@example.com')
        u.set_password('cat')
        self.assertTrue(u.check_password('cat'))
        self.assertFalse(u.check_password('dog'))

    def test_password_salts_are_random(self):
        u = User(username='john', email='john@example.com')
        u.set_password('cat')
        u2 = User(username='susan', email='susan@example.com')
        u2.set_password('cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_user_role(self):
        u = User(username='john', email='john@example.com', role='user')
        self.assertFalse(u.is_admin)
    
    def test_admin_role(self):
        u = User(username='admin', email='admin@example.com', role='admin')
        self.assertTrue(u.is_admin)
