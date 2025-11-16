from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum


db = SQLAlchemy()


# Enum for Ticket Status
class TicketStatus(enum.Enum):
    OPEN = 'Open'
    IN_PROGRESS = 'In Progress'
    CLOSED = 'Closed'


# NEW: SupportTicket Model
class SupportTicket(db.Model):
    """Model for storing support tickets."""
    __tablename__ = 'support_tickets'

    id = db.Column(db.String(20), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=True) # Optional invoice number
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to the user
    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True))


### Admin Model
class Admin(db.Model):
    """Admin model for storing administrator credentials."""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        """Hashes and sets the admin's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    

### User Model
class User(db.Model):
    """User model for storing user details."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    pan_number = db.Column(db.String(10), unique=True, nullable=False)

    password_hash = db.Column(db.String(256))
    
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade="all, delete-orphan")
    vendor_material_form = db.relationship('VendorMaterial', backref='user', uselist=False, cascade="all, delete-orphan")
    vendor_work_form = db.relationship('VendorWork', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


### Invoice Model
class Invoice(db.Model):
    """Invoice model for storing invoice details."""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False)
    # gst_number = db.Column(db.String(15), nullable=False)
    # pan_number = db.Column(db.String(10), nullable=False)
    po_number = db.Column(db.String(50))
    invoice_amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='In Review')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    payment_date = db.Column(db.DateTime, nullable=True)


### VendorMaterial Model
class VendorMaterial(db.Model):
    """Model for the material vendor form."""
    __tablename__ = 'vendor_material'
    
    id = db.Column(db.Integer, primary_key=True)
    # Section A
    vendor_name = db.Column(db.String(100), nullable=False)
    firm_type = db.Column(db.String(50), nullable=False)
    firm_type_other = db.Column(db.String(100), nullable=True)
    nature_of_business = db.Column(db.String(100))
    material_supplied = db.Column(db.String(100))
    establishment_date = db.Column(db.Date)
    pan_number = db.Column(db.String(10))
    gst_number = db.Column(db.String(15))
    
    # Section B
    office_address_1 = db.Column(db.String(255))
    office_address_2 = db.Column(db.String(255), nullable=True)
    office_city = db.Column(db.String(100))
    office_state = db.Column(db.String(100))
    office_pincode = db.Column(db.String(10))
    office_contact_person = db.Column(db.String(100))
    office_mobile = db.Column(db.String(20))
    office_email = db.Column(db.String(120))
    gst_address_1 = db.Column(db.String(255))
    gst_address_2 = db.Column(db.String(255), nullable=True)
    gst_city = db.Column(db.String(100))
    gst_state = db.Column(db.String(100))
    gst_pincode = db.Column(db.String(10))
    gst_contact_person = db.Column(db.String(100))
    gst_mobile = db.Column(db.String(20))
    gst_email = db.Column(db.String(120))

    # Section C
    account_holder_name = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    branch_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))

    # Section D
    primary_contact_name = db.Column(db.String(100))
    primary_contact_designation = db.Column(db.String(100))
    primary_contact_mobile = db.Column(db.String(20))
    primary_contact_email = db.Column(db.String(120))
    alternate_contact_name = db.Column(db.String(100), nullable=True)
    alternate_contact_designation = db.Column(db.String(100), nullable=True)
    alternate_contact_mobile = db.Column(db.String(20), nullable=True)
    alternate_contact_email = db.Column(db.String(120), nullable=True)

    # Section E
    work_category = db.Column(db.Text) # To store JSON string of categories
    work_category_other = db.Column(db.String(100), nullable=True) # ADDED

    # Attachments
    pan_card_copy_path = db.Column(db.String(255))
    gst_certificate_copy_path = db.Column(db.String(255))
    cancelled_cheque_copy_path = db.Column(db.String(255))
    address_proof_copy_path = db.Column(db.String(255))
    auth_letter_copy_path = db.Column(db.String(255), nullable=True)

    # Section F
    declaration_agreed = db.Column(db.Boolean)
    signature_name = db.Column(db.String(100))
    signature_date = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Under Review')


### VendorMaterial Model
class VendorWork(db.Model):
    """Model for the work vendor form."""
    __tablename__ = 'vendor_work'
    
    id = db.Column(db.Integer, primary_key=True)
    # Section A
    contractor_name = db.Column(db.String(100), nullable=False)
    firm_type = db.Column(db.String(50), nullable=False)
    firm_type_other = db.Column(db.String(100), nullable=True)
    scope_of_work = db.Column(db.String(200))
    nature_of_service = db.Column(db.String(100))
    establishment_date = db.Column(db.Date)
    pan_number = db.Column(db.String(10))
    gst_number = db.Column(db.String(15), nullable=True)
    pf_esic_registered = db.Column(db.String(10))
    pf_number = db.Column(db.String(50), nullable=True)
    esic_number = db.Column(db.String(50), nullable=True)

    # Section B
    office_address_1 = db.Column(db.String(255))
    office_address_2 = db.Column(db.String(255), nullable=True)
    office_city = db.Column(db.String(100))
    office_state = db.Column(db.String(100))
    office_pincode = db.Column(db.String(10))
    office_contact_person = db.Column(db.String(100))
    office_mobile = db.Column(db.String(20))
    office_email = db.Column(db.String(120))
    site_address_1 = db.Column(db.String(255), nullable=True)
    site_address_2 = db.Column(db.String(255), nullable=True)
    site_city = db.Column(db.String(100), nullable=True)
    site_state = db.Column(db.String(100), nullable=True)
    site_pincode = db.Column(db.String(10), nullable=True)
    site_contact_person = db.Column(db.String(100), nullable=True)
    site_mobile = db.Column(db.String(20), nullable=True)
    site_email = db.Column(db.String(120), nullable=True)

    # Section C
    account_holder_name = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    branch_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))

    # Section D
    skilled_labour_count = db.Column(db.Integer)
    unskilled_labour_count = db.Column(db.Integer)
    supervisor_count = db.Column(db.Integer)
    safety_officer = db.Column(db.String(10))
    gst_on_labour = db.Column(db.String(10))

    # Section E
    work_category = db.Column(db.Text)
    work_category_other = db.Column(db.String(100), nullable=True)
    # Section F
    years_experience = db.Column(db.Integer)
    major_clients = db.Column(db.Text)
    reference_contact = db.Column(db.String(255))
    project_experience = db.Column(db.String(50))
    
    # Attachments
    pan_card_copy_path = db.Column(db.String(255))
    proprietor_id_copy_path = db.Column(db.String(255))
    cancelled_cheque_copy_path = db.Column(db.String(255))
    address_proof_copy_path = db.Column(db.String(255))
    gst_certificate_copy_path = db.Column(db.String(255))
    pf_esic_copy_path = db.Column(db.String(255))
    work_orders_copy_path = db.Column(db.Text, nullable=True)

    # Section G
    declaration_agreed = db.Column(db.Boolean)
    signature_name = db.Column(db.String(100))
    signature_date = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Under Review')
