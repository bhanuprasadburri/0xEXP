from app import app
from models import User

with app.app_context():
    user = User.query.filter_by(email='bhanu@example.com').first()
    if not user:
        raise SystemExit('test user not found')

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    resp = client.get('/donor/dashboard')
    print(resp.status_code)
    print('dashboard' if resp.status_code == 200 else 'failed')
    if resp.status_code == 200:
        print('dashboard_fragment' if 'Welcome back' in resp.get_data(as_text=True) else 'fragment_missing')
