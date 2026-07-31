from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, NGO
from .donation import Donation, DonationHistory
from .notification import Notification
from .contact import ContactMessage
