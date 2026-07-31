from app import app

client = app.test_client()
resp_login = client.get('/login')
resp_register = client.get('/register')
print('login_status', resp_login.status_code)
print('register_status', resp_register.status_code)
print('login_has_email_field', 'name="email"' in resp_login.get_data(as_text=True))
print('register_has_donor_cta', 'Register as Donor' in resp_register.get_data(as_text=True))
