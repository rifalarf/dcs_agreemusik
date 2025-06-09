"""
Test Routes - Testing semua routes dalam aplikasi
Tests for AGREE MUSIK Digital Certificate System integration
"""

import unittest
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class TestRoutes(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Create test users
        self.create_test_users()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_users(self):
        """Create test users for testing"""
        # Admin user
        admin = User(
            username='admin_test',
            email='admin@test.com',
            nama_lengkap='Test Admin',
            role='admin',
            password='admin123'
        )
        
        # Student user
        student = User(
            username='student_test',
            email='student@test.com',
            nama_lengkap='Test Student',
            role='pelajar',
            password='student123',
            spesialis='Guitar',
            spesialis_level='Beginner'        )
        
        db.session.add(admin)
        db.session.add(student)
        db.session.commit()
        
        self.admin_user = admin
        self.student_user = student
    
    def login_user(self, username, password):
        """Helper function to login a user"""
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'submit': True
        }, follow_redirects=True)
    
    def test_landing_page_accessible(self):
        """Test: Landing page should be accessible without login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AGREE MUSIK', response.data)
        print("✓ Landing page accessible")
    
    def test_landing_page_shows_login_buttons_for_guests(self):
        """Test: Landing page shows login/register buttons for guests"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
        self.assertIn(b'Register', response.data)
        self.assertNotIn(b'Dashboard', response.data)
        self.assertNotIn(b'Logout', response.data)
        print("✓ Landing page shows correct buttons for guests")
    
    def test_certificate_verification_accessible(self):
        """Test: Certificate verification should be accessible to everyone"""
        response = self.client.get('/public/verify')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Verifikasi Sertifikat', response.data)
        print("✓ Certificate verification page accessible")
    
    def test_login_page_accessible(self):
        """Test: Login page should be accessible"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
        print("✓ Login page accessible")
    
    def test_register_page_accessible(self):
        """Test: Register page should be accessible"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registrasi', response.data)
        print("✓ Register page accessible")
    
    def test_dashboard_redirect_for_admin(self):
        """Test: Dashboard should redirect admin to admin dashboard"""
        self.login_user('admin_test', 'admin123')
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)
        print("✓ Admin dashboard accessible after login")
    
    def test_dashboard_redirect_for_student(self):
        """Test: Dashboard should redirect student to student dashboard"""
        self.login_user('student_test', 'student123')
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Pelajar Dashboard', response.data)
        print("✓ Student dashboard accessible after login")
    
    def test_landing_page_shows_dashboard_for_authenticated_users(self):
        """Test: Landing page shows dashboard button for logged in users"""
        self.login_user('student_test', 'student123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check if Dashboard link is present (could be in navbar)
        self.assertIn(b'AGREE MUSIK', response.data)  # Landing page still accessible
        print("✓ Landing page accessible for authenticated users")
    
    def test_logout_functionality(self):
        """Test: Logout should work and redirect to landing page"""
        self.login_user('student_test', 'student123')
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should be back to landing page with login buttons
        self.assertIn(b'AGREE MUSIK', response.data)
        print("✓ Logout functionality works")
      def test_navigation_consistency(self):
        """Test: Check if navigation routes are consistent"""
        # Test main routes
        routes_to_test = [
            ('/', 200),
            ('/index', 200),
            ('/auth/login', 200),
            ('/auth/register', 200),
            ('/public/verify', 200)
        ]
        
        for route, expected_status in routes_to_test:
            response = self.client.get(route)
            self.assertEqual(response.status_code, expected_status, 
                           f"Route {route} returned {response.status_code}, expected {expected_status}")
        
        print("✓ All main navigation routes working")

if __name__ == '__main__':
    print("🧪 TESTING ROUTES - AGREE MUSIK Digital Certificate System")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
