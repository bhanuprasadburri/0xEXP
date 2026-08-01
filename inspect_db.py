import sqlite3
p = r'C:\Users\bhanu\Desktop\0xExp\instance\0xexp.db'
conn = sqlite3.connect(p)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print('TABLES')
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(row['name'])
print('\nUSERS')
for row in cur.execute("SELECT id, full_name, name, email, phone, role, organization_name, address, created_at FROM users ORDER BY id"):
    print(dict(row))
print('\nCONTACT_MESSAGES')
for row in cur.execute("SELECT id, name, email, subject, message, created_at FROM contact_messages ORDER BY id"):
    print(dict(row))
print('\nDONATIONS')
for row in cur.execute("SELECT id, donor_id, ngo_id, food_name, quantity, servings, status, pickup_address, created_at FROM donations ORDER BY id"):
    print(dict(row))
print('\nNOTIFICATIONS')
for row in cur.execute("SELECT id, user_id, title, message, status, is_read, created_at FROM notifications ORDER BY id"):
    print(dict(row))
conn.close()
