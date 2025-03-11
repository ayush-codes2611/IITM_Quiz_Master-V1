from datetime import date, datetime, timezone
from controllers import db, login_manager
from flask_login import UserMixin
from sqlalchemy import CheckConstraint

# Function to load user based on ID and role
@login_manager.user_loader
def load_user(user_id):
    try:
        user_type, id = user_id.split('-')
        id = int(id)
        if user_type == 'admin':
            return Admin.query.get(id)
        elif user_type == 'professional':
            return Professional.query.get(id)
        elif user_type == 'customer':
            return Customer.query.get(id)
    except (ValueError, AttributeError):
        print(f"ERROR: Invalid user_id: {user_id}")
        return None


from datetime import date, datetime, timezone
from controllers import db, login_manager
from flask_login import UserMixin
from sqlalchemy import CheckConstraint

# # Function to load user based on ID and role
# @login_manager.user_loader
# def load_user(user_id):
#     try:
#         user_type, id = user_id.split('-')
#         id = int(id)
#         if user_type == 'admin':
#             return Admin.query.get(id)
#         elif user_type == 'professional':
#             return Professional.query.get(id)
#         elif user_type == 'customer':
#             return Customer.query.get(id)
#     except (ValueError, AttributeError):
#         print(f"ERROR: Invalid user_id: {user_id}")
#         return None


class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"<Email={self.email}>"
    def get_id(self):
        return f"admin-{self.id}"
    
    
class Customer(db.Model, UserMixin):
    __tablename__ = 'customers'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=50), nullable=False, unique=True)
    email=db.Column(db.String(length=50), nullable=False, unique=True)
    password = db.Column(db.String(length=60), nullable=False)
    fullname = db.Column(db.String(length=100), nullable=False)
    address = db.Column(db.String(length=255), nullable=False)
    pin_code = db.Column(db.String(length=10), nullable=False)
    contact_no = db.Column(db.String(length=10), nullable=False, unique=True)
    document_path = db.Column(db.String(length=200), nullable=False)  # Path to uploaded document
    is_approved = db.Column(db.Boolean, default=True)
    # date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # def __repr__(self):
    #     return f"<Customer ID={self.id}, Username='{self.username}', Name='{self.fullname}'>"
    def get_id(self):
        return f"customer-{self.id}"



class Professional(db.Model, UserMixin):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=50), nullable=False, unique=True)
    email=db.Column(db.String(length=50), nullable=False, unique=True)
    password= db.Column(db.String(length=60), nullable=False)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    service_type = db.Column(db.String(length=50), nullable=False)
    experience = db.Column(db.String(length=50), nullable=False)
    description = db.Column(db.Text, nullable=False, unique=True)
    document_path = db.Column(db.String(length=200), nullable=False)  # Path to uploaded document
    is_approved = db.Column(db.Boolean, default=False)  # Approval status
    # date_created = db.Column(db.Date, default=date.today)
    admin_comment = db.Column(db.Text, nullable=True)  # Admin comment for feedback
    contact_no = db.Column(db.String(length=10), nullable=False, unique=True)
    professional_rating = db.Column(db.Float, default=0.0, nullable=False)
    rating_count = db.Column(db.Integer, default=0, nullable=False)

    # Ensure professional_rating is between 0 and 5
    __table_args__ = (
        CheckConstraint('professional_rating BETWEEN 0 AND 5', name='check_professional_rating_range'),
    )

    def __repr__(self):
        return f'Professional {self.name}'
    def get_id(self):
        return f"professional-{self.id}"
    
class ServiceLocation(db.Model):
    __tablename__ = 'service_locations'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    pin_code = db.Column(db.String(6), nullable=False) # 6-digit pins only
    service = db.relationship('Service', back_populates='locations')
    def __repr__(self):
        return f"{self.pin_code}"


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) #needs to put the unique
    base_price = db.Column(db.Float(), nullable=False)
    time_required = db.Column(db.String(50), nullable=False)
    srv_category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False, default="Default description")

    locations = db.relationship('ServiceLocation', back_populates='service', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service ID={self.id}, Name='{self.name}', Price={self.base_price}>"
   

class ServiceRequests(db.Model):
    __tablename__ = 'service_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key relationships
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete="CASCADE"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)  # Nullable until assigned
    
    # Date fields
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    
    # Status and remarks
    service_status = db.Column(db.String(20), nullable=False, default="requested")  # Default status
    remarks = db.Column(db.Text, nullable=True)
    service_rating = db.Column(db.Integer, nullable=True)
    
    # Relationships (optional, for ease of accessing related data)
    service = db.relationship("Service", backref="requests", lazy=True)
    professional = db.relationship("Professional", backref="requests", lazy=True)
    customer = db.relationship("Customer", backref="requests", lazy=True)

    
    # Ensure the service rating is between 0 and 5
    __table_args__ = (
        CheckConstraint('service_rating IS NULL OR service_rating BETWEEN 0 AND 5', name='check_service_rating_range'),
    )

    def __repr__(self):
        return (f"<ServiceRequests ID={self.id}, Service ID={self.service_id}, "
                f"Customer ID={self.customer_id}, Professional ID={self.professional_id}, "
                f"Status='{self.service_status}'>")