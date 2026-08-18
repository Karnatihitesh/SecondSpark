import unittest
from app import create_app
from app.models import db, User, Project, Category, VerificationCode, Transaction
from seed_data import seed_database

class SecondSparkTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        seed_database(cls.app)

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        self.client = self.app.test_client()
        try:
            self.client.cookie_jar.clear()
        except Exception:
            pass

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Give Unfinished Ideas a', response.data)
        self.assertIn(b'SecondSpark', response.data)

    def test_browse_projects(self):
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Discover Projects', response.data)

    def test_search_api(self):
        response = self.client.get('/api/search?q=LiDAR')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(len(json_data['results']) >= 1)
        self.assertIn('Autonomous LiDAR Lawn Mower', json_data['results'][0]['title'])

    def test_project_details(self):
        first_proj = Project.query.first()
        self.assertIsNotNone(first_proj)
        response = self.client.get(f'/projects/{first_proj.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(first_proj.title.encode('utf-8'), response.data)
        self.assertIn(b'Stalled Issue & Faults to Solve', response.data)

    def test_about_and_team(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Karnati Hitesh', response.data)
        self.assertIn(b'Sadineni Mrudul', response.data)
        self.assertIn(b'Annepalli Jashwanth Reddy', response.data)
        self.assertIn(b'Siripanga Manikumar', response.data)
        self.assertIn(b'Nandala Supriya', response.data)
        self.assertIn(b'Mamidi Vydhika', response.data)

    def test_contact_page(self):
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'karnatihitesh@gmail.com', response.data)
        self.assertIn(b'+91 9490682602', response.data)

    def test_reviews_page(self):
        response = self.client.get('/reviews/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Maker Reviews', response.data)

    def test_forgot_password_otp_flow(self):
        # 1. Request OTP for existing user
        response = self.client.post('/auth/forgot-password', data={
            'email': 'alex@secondspark.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify OTP was created in DB
        otp = VerificationCode.query.filter_by(email='alex@secondspark.com', is_used=False).first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.code), 6)

        # 2. Verify OTP
        verify_res = self.client.post('/auth/verify-otp', data={
            'email': 'alex@secondspark.com',
            'otp_code': otp.code
        }, follow_redirects=True)
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn(b'Set New Password', verify_res.data)

        # 3. Reset Password
        with self.client.session_transaction() as sess:
            reset_token = sess.get('reset_token')
        
        reset_res = self.client.post('/auth/reset-password', data={
            'email': 'alex@secondspark.com',
            'token': reset_token,
            'new_password': 'NewPassword@2026',
            'confirm_password': 'NewPassword@2026'
        }, follow_redirects=True)
        self.assertEqual(reset_res.status_code, 200)
        self.assertIn(b'Password updated successfully', reset_res.data)

        # 4. Login with new password
        login_res = self.client.post('/auth/login', data={
            'login_input': 'alex@secondspark.com',
            'password': 'NewPassword@2026'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Dashboard', login_res.data)

    def test_upi_payment_and_commission_split(self):
        # Test 2% commission calculation
        comm, net = Transaction.compute_split(1000.0)
        self.assertEqual(comm, 20.0)
        self.assertEqual(net, 980.0)

        comm, net = Transaction.compute_split(500.0)
        self.assertEqual(comm, 10.0)
        self.assertEqual(net, 490.0)

        # Login as helper user
        self.client.post('/auth/login', data={
            'login_input': 'priya_sharma',
            'password': 'Priya@12345'
        }, follow_redirects=True)

        priya = User.query.filter_by(username='priya_sharma').first()
        proj = Project.query.filter(Project.user_id != priya.id).first()
        self.assertIsNotNone(proj)

        # Checkout page
        checkout_res = self.client.get(f'/payments/checkout/{proj.id}')
        self.assertEqual(checkout_res.status_code, 200)
        self.assertIn(b'Secure Checkout', checkout_res.data)

        # Initiate payment
        init_res = self.client.post('/payments/initiate', data={
            'project_id': proj.id,
            'amount': 1500,
            'gateway': 'gateway1',
            'agreed': 'on'
        }, follow_redirects=True)
        self.assertEqual(init_res.status_code, 200)
        self.assertIn(b'Complete Your Payment', init_res.data)
        self.assertIn(b'secondspark@oksbi', init_res.data)

        # Confirm UTR
        with self.client.session_transaction() as sess:
            order_id = sess.get('pending_order_id')
        
        confirm_res = self.client.post('/payments/confirm', data={
            'order_id': order_id,
            'utr': 'UPI492837190412'
        }, follow_redirects=True)
        self.assertEqual(confirm_res.status_code, 200)
        self.assertIn(b'Payment Confirmed', confirm_res.data)

        # Verify transaction status in DB
        txn = Transaction.query.filter_by(order_id=order_id).first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.status, 'Completed')
        self.assertEqual(txn.amount_inr, 1500.0)
        self.assertEqual(txn.commission_inr, 30.0)  # 2% of 1500
        self.assertEqual(txn.net_amount_inr, 1470.0)

    def test_login_and_admin_security(self):
        # Unauthenticated admin access should redirect to login
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

        # Logout any existing session
        self.client.get('/auth/logout')

        # Admin user login
        admin_login = self.client.post('/auth/login', data={
            'login_input': 'admin',
            'password': 'Admin@12345'
        }, follow_redirects=True)
        self.assertEqual(admin_login.status_code, 200)

        # Admin accessing admin portal should succeed
        admin_ok = self.client.get('/admin/')
        self.assertEqual(admin_ok.status_code, 200)
        self.assertIn(b'Platform Moderation & Control', admin_ok.data)

if __name__ == '__main__':
    unittest.main()
