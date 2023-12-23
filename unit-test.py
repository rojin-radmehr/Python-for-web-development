import unittest
from app import check_coor,app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()



        
    def test_welcome_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        
    def test_login(self):
        response = self.app.post('/login', data={'username': 'someuser', 'password': 'somepwd'})
        self.assertEqual(response.status_code, 200)
        
        
    def test_valid_format1(self):
        coor = "Latitude: 40.7128 Longitude: -74.0060"
        result = check_coor(coor)
        self.assertEqual(result, (40.7128, -74.0060))

    def test_valid_format2(self):
        coor = "36.7783, -119.4179"
        result = check_coor(coor)
        self.assertEqual(result, (36.7783, -119.4179))

    def test_valid_format3(self):
        coor = "[51.5074, -0.1278]"
        result = check_coor(coor)
        self.assertEqual(result, (51.5074, -0.1278))

    def test_invalid_format1(self):
        coor = "Invalid Format"
        result = check_coor(coor)
        self.assertIsNone(result)

    def test_invalid_format2(self):
        coor = "Latitude: invalid Longitude: 123.45"
        result = check_coor(coor)
        self.assertIsNone(result)
    
if __name__ == '__main__':
    unittest.main()
        
    