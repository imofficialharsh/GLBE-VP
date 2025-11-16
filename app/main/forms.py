from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (StringField, TextAreaField, DecimalField, RadioField, 
                     DateField, TelField, EmailField, SelectMultipleField, 
                     BooleanField, widgets, IntegerField, SelectField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError


#InvoiceForm
class InvoiceForm(FlaskForm):
    """Form for uploading invoices."""
    invoice_number = StringField('Invoice Number', validators=[DataRequired(), Length(max=20)])
    
    # gst_number = StringField('GST Number', validators=[
    #     DataRequired(), 
    #     Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GST Number format.')
    # ])
    # pan_number = StringField('PAN Number', validators=[
    #     DataRequired(), 
    #     Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN Number format.')
    # ])

    po_number = StringField('PO Number', validators=[DataRequired(), Length(max=20)])
    
    invoice_amount = DecimalField('Invoice Amount (INR)', validators=[DataRequired()])
    
    description = TextAreaField('Brief Description', validators=[Optional(), Length(max=70)])
    
    invoice_file = FileField('Upload Invoice File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Only PDF and image files are allowed!')
    ])


#VendorMaterialForm
class VendorMaterialForm(FlaskForm):
    """Defines the fields and validators for the material vendor form."""
    
    # Section A
    vendor_name = StringField('Vendor Name', validators=[DataRequired(), Length(max=100)])
    firm_type = RadioField('Type of Firm', choices=[
        ('Proprietorship', 'Proprietorship'), ('Partnership', 'Partnership'),
        ('Pvt_Ltd', 'Pvt Ltd'), ('LLP', 'LLP'), ('Others', 'Others')
    ], validators=[DataRequired()])
    firm_type_other = StringField('If Other, specify', validators=[Optional()])
    nature_of_business = StringField('Nature of Business', validators=[DataRequired(), Length(max=100)])
    material_supplied = StringField('Type of Material Supplied', validators=[DataRequired(), Length(max=100)])
    establishment_date = DateField('Date of Establishment', format='%Y-%m-%d', validators=[DataRequired()])
    pan_number = StringField('PAN Number', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN format.')])
    gst_number = StringField('GST Number', validators=[DataRequired(), Length(min=15, max=15), Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GST format.')])

    # Section B - Office Address
    office_address_1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    office_address_2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    office_city = StringField('City', validators=[DataRequired(), Length(max=100)])
    office_state = StringField('State', validators=[DataRequired(), Length(max=100)])
    office_pincode = StringField('PIN Code', validators=[DataRequired(), Length(min=6, max=6)])
    office_contact_person = StringField('Contact Person', validators=[DataRequired(), Length(max=100)])
    office_mobile = TelField('Mobile Number', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^\d{10}$', message='Invalid 10-digit mobile number.')])
    office_email = EmailField('Email ID', validators=[DataRequired(), Email()])

    # Section B - GST Address
    gst_address_1 = StringField('Address Line 1', validators=[Optional(), Length(max=255)])
    gst_address_2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    gst_city = StringField('City', validators=[Optional(), Length(max=100)])
    gst_state = StringField('State', validators=[Optional(), Length(max=100)])
    gst_pincode = StringField('PIN Code', validators=[Optional(), Length(min=6, max=6)])
    gst_contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    gst_mobile = TelField('Mobile Number', validators=[Optional(), Length(min=10, max=10), Regexp(r'^\d{10}$', message='Invalid 10-digit mobile number.')])
    gst_email = EmailField('Email ID', validators=[Optional(), Email()])

    # Section C - Bank Details
    account_holder_name = StringField('Account Holder Name', validators=[DataRequired(), Length(max=100)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    branch_name = StringField('Branch Name', validators=[DataRequired(), Length(max=100)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=9, max=18)])
    ifsc_code = StringField('IFSC Code', validators=[DataRequired(), Length(min=11, max=11), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$', message='Invalid IFSC code format.')])

    # Section D - Primary Contact
    primary_contact_name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    primary_contact_designation = StringField('Designation', validators=[DataRequired(), Length(max=100)])
    primary_contact_mobile = TelField('Mobile Number', validators=[DataRequired(), Regexp(r'^\d{10}$')])
    primary_contact_email = EmailField('Email ID', validators=[DataRequired(), Email()])
    
    # Section D - Alternate Contact (Optional)
    alternate_contact_name = StringField('Name', validators=[Optional(), Length(max=100)])
    alternate_contact_designation = StringField('Designation', validators=[Optional(), Length(max=100)])
    alternate_contact_mobile = TelField('Mobile Number', validators=[Optional(), Length(min=10, max=10), Regexp(r'^\d{10}$')])
    alternate_contact_email = EmailField('Email ID', validators=[Optional(), Email()])
    
    # Section E - Work Category Checkboxes
    work_category = SelectMultipleField('Type of Work / Category', 
        choices=[
            ('Cement', 'Cement Supplier'), ('Steel', 'Steel Supplier'),
            ('Stone_Marble_Granite', 'Stone/Marble/Granite'), ('Tiles_Flooring', 'Tiles / Flooring'),
            ('Wood_Ply_Carpentry', 'Wood/Ply/Carpentry'), ('Plumbing_Sanitary', 'Plumbing / Sanitary'),
            ('Electrical_Lighting', 'Electrical / Lighting'), ('Paint_Finishing', 'Paint / Finishing'),
            ('Safety_Equipment', 'Safety Equipment'), ('Other', 'Miscellaneous')
        ],
        widget=widgets.ListWidget(prefix_label=False), 
        option_widget=widgets.CheckboxInput(),
        validators=[DataRequired(message="Please select at least one category.")]
    )
    work_category_other = StringField('If Miscellaneous, specify', validators=[Optional()])

    # Attachments
    pan_card_copy = FileField('PAN Card Copy', validators=[
        FileRequired(), 
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')
    ])
    gst_certificate_copy = FileField('GST Certificate', validators=[
        FileRequired(), 
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')
    ])
    cancelled_cheque_copy = FileField('Cancelled Cheque', validators=[
        FileRequired(), 
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')
    ])
    address_proof_copy = FileField('Address Proof', validators=[
        FileRequired(), 
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')
    ])
    auth_letter_copy = FileField('Authorization Letter (if applicable)', validators=[
        Optional(), 
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])

    # Section F
    declaration_agreed = BooleanField('I agree to the declarations.', validators=[DataRequired(message="You must agree to the declarations to proceed.")])
    signature_name = StringField('Signature of Vendor', validators=[DataRequired()])
    signature_date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])


#VendorWorkForm
class VendorWorkForm(FlaskForm):
    """Defines the fields and validators for the work vendor form."""
    
    # Section A
    contractor_name = StringField('Contractor Name', validators=[DataRequired(), Length(max=100)])
    firm_type = RadioField('Type of Firm', choices=[
        ('Proprietorship', 'Proprietorship'), ('Partnership', 'Partnership'),
        ('Pvt_Ltd', 'Pvt Ltd'), ('LLP', 'LLP'), ('Others', 'Others')
    ], validators=[DataRequired()])
    firm_type_other = StringField('If Other, specify', validators=[Optional()])
    scope_of_work = StringField('Scope of Work', validators=[DataRequired(), Length(max=200)])
    nature_of_service = StringField('Nature of Service', validators=[DataRequired(), Length(max=100)])
    establishment_date = DateField('Date of Establishment', format='%Y-%m-%d', validators=[DataRequired()])
    pan_number = StringField('PAN Number', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN format.')])
    gst_number = StringField('GST Number', validators=[Optional(), Length(min=15, max=15), Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GST format.')])
    pf_esic_registered = RadioField('PF / ESIC Registered', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[DataRequired()])
    pf_number = StringField('PF No', validators=[Optional(), Length(max=12)])
    esic_number = StringField('ESIC No', validators=[Optional(), Length(max=17)])

    # Section B - Office Address
    office_address_1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    office_address_2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    office_city = StringField('City', validators=[DataRequired(), Length(max=100)])
    office_state = StringField('State', validators=[DataRequired(), Length(max=100)])
    office_pincode = StringField('PIN Code', validators=[DataRequired(), Length(min=6, max=6)])
    office_contact_person = StringField('Contact Person', validators=[DataRequired(), Length(max=100)])
    office_mobile = TelField('Mobile Number', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^\d{10}$')])
    office_email = EmailField('Email ID', validators=[DataRequired(), Email()])

    # Section B - Site Address
    site_address_1 = StringField('Address Line 1', validators=[Optional(), Length(max=255)])
    site_address_2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    site_city = StringField('City', validators=[Optional(), Length(max=100)])
    site_state = StringField('State', validators=[Optional(), Length(max=100)])
    site_pincode = StringField('PIN Code', validators=[Optional(), Length(min=6, max=6)])
    site_contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    site_mobile = TelField('Mobile Number', validators=[Optional(), Length(min=10, max=10), Regexp(r'^\d{10}$')])
    site_email = EmailField('Email ID', validators=[Optional(), Email()])

    # Section C - Bank Details
    account_holder_name = StringField('Account Holder Name', validators=[DataRequired(), Length(max=100)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    branch_name = StringField('Branch Name', validators=[DataRequired(), Length(max=100)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=9, max=18)])
    ifsc_code = StringField('IFSC Code', validators=[DataRequired(), Length(min=11, max=11), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$')])

    # Section D - Labour Details
    skilled_labour_count = IntegerField('Approx. Number of Skilled Labour', validators=[DataRequired()])
    unskilled_labour_count = IntegerField('Approx. Number of Unskilled Labour', validators=[DataRequired()])
    supervisor_count = IntegerField('Approx. Number of Supervisors / Engineers', validators=[DataRequired()])
    safety_officer = RadioField('Safety Officer', choices=[('yes', 'Yes'), ('no', 'No')], validators=[DataRequired()])
    gst_on_labour = RadioField('GST Applicable on Labour Billing', choices=[('yes', 'Yes'), ('no', 'No')], validators=[DataRequired()])

    # Section E - Work Categories
    work_category = SelectMultipleField('Work Categories',
        choices=[
            ('Civil_Work', 'Civil Work Contractor'), ('Electrical_Work', 'Electrical Work Contractor'),
            ('Plumbing_Sanitary', 'Plumbing / Sanitary'), ('Fabrication_Ms', 'Fabrication / MS Work'),
            ('Tiling_Flooring', 'Tiling / Flooring'), ('Waterproofing', 'Waterproofing'),
            ('Labour_Supply', 'Labour Supply'), ('Painting_Finishing', 'Painting / Finishing'),
            ('Phe_Stp_Etp', 'PHE / STP / ETP Works'), ('Road_Paving', 'Road & Paving'), ('Other', 'Miscellaneous')
        ],
        widget=widgets.ListWidget(prefix_label=False), 
        option_widget=widgets.CheckboxInput(),
        validators=[DataRequired(message="Please select at least one category.")]
    )
    work_category_other = StringField('If Miscellaneous, specify', validators=[Optional()])

    # Section F - Past Experience
    years_experience = IntegerField('Years of Experience', validators=[DataRequired()])
    major_clients = TextAreaField('Major Clients Worked With', validators=[DataRequired()])
    reference_contact = StringField('Reference Contact (Name, Company, Mobile)', validators=[DataRequired()])
    project_experience = RadioField('Project Type Experience', choices=[
        ('Govt', 'Govt. Projects'), ('Pvt', 'Pvt. Projects'), ('Both', 'Both')
    ], validators=[DataRequired()])

    # Attachments
    pan_card_copy = FileField('PAN Card', validators=[FileRequired(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')
    ])
    proprietor_id_copy = FileField('Aadhar Card', validators=[FileRequired(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'])])
    cancelled_cheque_copy = FileField('Cancelled Cheque', validators=[FileRequired(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])
    address_proof_copy = FileField('Address Proof', validators=[FileRequired(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])
    gst_certificate_copy = FileField('GST Certificate', validators=[Optional(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])
    pf_esic_copy = FileField('PF/ESIC Certificate', validators=[Optional(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])
    work_orders_copy = FileField('Work Orders / Completion Certificates', validators=[Optional(), FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Images and PDFs only!')])

    # Section G
    declaration_agreed = BooleanField('I agree to the declarations.', validators=[DataRequired(message="You must agree to the declarations to proceed.")])
    signature_name = StringField('Signature of Vendor', validators=[DataRequired()])
    signature_date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])


#SupportTicketForm
class SupportTicketForm(FlaskForm):
    """Form for raising a support ticket."""
    category = SelectField('Category', choices=[
        ('', 'Please select a category...'),
        ('Payment Query', 'Payment Query'),
        ('Technical Error', 'Technical Error'),
        ('Invoice Rejection', 'Invoice Rejection'),
        ('General Question', 'General Question')
    ], validators=[DataRequired(message="Please select a category.")])

    invoice_no = StringField('Invoice No.', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=70)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=200)])

    submit = SubmitField('Submit Ticket')

    # Custom validator to make invoice_no required for specific categories
    def validate_invoice_no(form, field):
        if form.category.data in ['Payment Query', 'Invoice Rejection'] and not field.data:
            raise ValidationError('Invoice No. is required for this category.')