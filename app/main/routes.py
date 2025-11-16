from flask import (
    Blueprint, render_template, session, redirect, url_for,
    request, flash, current_app, send_from_directory, g
)
from app.models import db, Invoice, User, VendorMaterial, VendorWork, SupportTicket, TicketStatus
import os
from sqlalchemy import or_, func
from functools import wraps
import traceback
import json
import uuid
from .forms import InvoiceForm, VendorMaterialForm, VendorWorkForm, SupportTicketForm
from werkzeug.utils import secure_filename
from datetime import datetime
import secrets
import magic
import pytz
from datetime import datetime


main_bp = Blueprint('main', __name__, template_folder='../templates')

def save_file(file, subfolder):
    """
    Saves an uploaded file securely to a specified subfolder.
    [IMPROVEMENT] Now includes MIME type validation to prevent content spoofing.
    """
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)

    # File Extension Validation ---
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg', 'docx'})
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash(f"Invalid file type for {filename}. Allowed types: {', '.join(allowed_extensions)}", 'error')
        return None
    
    allowed_mime_types = current_app.config.get('ALLOWED_MIME_TYPES')

    # Read the first 2KB to check the "magic bytes"
    file_head = file.stream.read(2048)
    file.stream.seek(0)
    try:
        mime_type = magic.from_buffer(file_head, mime=True)
    except Exception as e:
        current_app.logger.warning(f"Could not determine MIME type for {filename}: {e}")
        mime_type = None

    if mime_type not in allowed_mime_types:
        flash(f"Invalid file content for {filename}. File appears to be a '{mime_type}' but only {', '.join(allowed_mime_types)} are allowed.", 'error')
        return None

    # File Size Validation ---
    max_size = current_app.config.get('MAX_FILE_SIZE_MB', 5) * 1024 * 1024
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0, os.SEEK_SET)
    if file_length > max_size:
         flash(f"File '{filename}' exceeds the maximum size limit of {max_size / (1024*1024)}MB.", 'error')
         return None

    # Unique Filename and Saving ---
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, unique_filename)

    try:
        file.save(file_path)
        return unique_filename
    except Exception as e:
        current_app.logger.error(f"Failed to save file {unique_filename} to {target_dir}: {e}")
        flash(f"An error occurred while saving the file: {filename}", 'error')
        return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Decorator for loading user ---
def user_required(f):
    """
    Checks for a valid logged-in user and loads their User object into g.user.
    This decorator should come *after* @login_required.
    It removes repetitive user-loading code from routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: 
             flash('Session error. Please log in again.', 'error')
             return redirect(url_for('auth.login'))

        user = db.session.get(User, session['user_id'])
        if not user:
            flash("Your user account was not found. Please log in again.", "error")
            session.clear()
            return redirect(url_for('auth.logout'))

        g.user = user 
        return f(*args, **kwargs)
    return decorated_function


def user_or_admin_required(f):
    """Ensures that EITHER a logged-in vendor OR an admin can access a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'admin_id' not in session:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@main_bp.context_processor
def inject_form_status():
    """Injects vendor form submission status into templates."""
    if 'user_id' in session:
        user_id = session['user_id']
        material_form_filled = VendorMaterial.query.filter_by(user_id=user_id).first() is not None
        work_form_filled = VendorWork.query.filter_by(user_id=user_id).first() is not None
        return dict(material_form_filled=material_form_filled, work_form_filled=work_form_filled)
    return dict(material_form_filled=False, work_form_filled=False)


##
@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    user = g.user
    user_id = user.id

    status_counts_results = db.session.query(
            Invoice.status,
            func.count(Invoice.status)
        ).filter_by(user_id=user_id).group_by(Invoice.status).all()

    counts = dict(status_counts_results)

    total_invoices_count = sum(counts.values())
    in_review_invoices_count = counts.get('In Review', 0)
    approved_invoices_count = counts.get('Approved', 0)
    paid_invoices_count = counts.get('Paid', 0)
    rejected_invoices_count = counts.get('Rejected', 0)

    total_business_value = db.session.query(func.sum(Invoice.invoice_amount))\
        .filter(Invoice.user_id == user_id, Invoice.status == 'Paid')\
        .scalar() or 0.0

    recent_payments = Invoice.query.filter(Invoice.user_id == user_id, Invoice.status == 'Paid', Invoice.payment_date != None)\
        .order_by(Invoice.payment_date.desc())\
        .limit(2).all()

    recent_invoices = Invoice.query.filter_by(user_id=user_id).order_by(Invoice.submission_date.desc()).limit(2).all()

    local_tz = pytz.timezone('Asia/Kolkata')

    recent_activities = []
    for inv in recent_invoices:
        activity_type = 'upload'
        if inv.status == 'Approved': activity_type = 'approved'
        elif inv.status == 'Paid': activity_type = 'paid'
        elif inv.status == 'Rejected': activity_type = 'rejected'

        utc_timestamp = inv.payment_date if inv.status == 'Paid' and inv.payment_date else inv.submission_date

        # 4. CONVERT IT TO LOCAL TIME
        local_timestamp = utc_timestamp # Default
        if utc_timestamp:
            # Tell Python the time is UTC, then convert to your local timezone
            local_timestamp = utc_timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz)

        recent_activities.append({
            'type': activity_type,
            'invoice_id': inv.id,
            'invoice_number': inv.invoice_number,
            'timestamp': local_timestamp
        })

    material_form = VendorMaterial.query.filter_by(user_id=user_id).first()
    work_form = VendorWork.query.filter_by(user_id=user_id).first()
    profile_status = 'Incomplete'
    if material_form: profile_status = material_form.status
    elif work_form: profile_status = work_form.status

    return render_template('dashboard.html',
                           user=user,
                           total_invoices_count=total_invoices_count,
                           in_review_invoices_count=in_review_invoices_count,
                           approved_invoices_count=approved_invoices_count,
                           paid_invoices_count=paid_invoices_count,
                           rejected_invoices_count=rejected_invoices_count,
                           total_business_value=total_business_value,
                           recent_payments=recent_payments,
                           recent_activities=sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:5],
                           profile_status=profile_status
                           )


##
@main_bp.route('/your-profile')
@login_required
@user_required
def your_profile():
    user = g.user
    material_form = VendorMaterial.query.filter_by(user_id=user.id).first()
    work_form = VendorWork.query.filter_by(user_id=user.id).first()

    profile_status = 'Incomplete'
    if material_form: profile_status = material_form.status
    elif work_form: profile_status = work_form.status

    return render_template('your-profile.html',
                           user=user,
                           material_form=material_form,
                           work_form=work_form,
                           profile_status=profile_status)


##
@main_bp.route('/upload-invoices', methods=['GET', 'POST'])
@login_required
@user_required
def upload_invoices():
    form = InvoiceForm()
    user = g.user

    is_registered = VendorMaterial.query.filter_by(user_id=user.id).first() or \
                    VendorWork.query.filter_by(user_id=user.id).first()
    
    if not is_registered:
        flash('Please complete your vendor registration form before uploading invoices.', 'warning')
        
    else:
        if form.validate_on_submit():
            invoice_num_from_form = form.invoice_number.data
            
            existing_invoice = Invoice.query.filter_by(
                invoice_number=invoice_num_from_form,
                user_id=user.id
            ).first()

            if existing_invoice:
                flash(f'Error: You have already uploaded an invoice with the number "{invoice_num_from_form}".', 'error')
            
            else: 
                file = form.invoice_file.data
                
                saved_filename = save_file(file, 'invoices') 

                if saved_filename:
                    try:
                        new_invoice = Invoice(
                            invoice_number=form.invoice_number.data,
                            po_number=form.po_number.data,
                            invoice_amount=float(form.invoice_amount.data),
                            description=form.description.data,
                            file_path=saved_filename,
                            user_id=user.id,
                            submission_date=datetime.utcnow()
                        )
                        db.session.add(new_invoice)
                        db.session.commit()
                        flash(f'Invoice "{invoice_num_from_form}" uploaded successfully!', 'success')
                        return redirect(url_for('main.upload_invoices'))
                    
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"Error saving invoice for user {user.id}: {e}\n{traceback.format_exc()}")
                        flash('An error occurred while saving the invoice. Please try again.', 'error')

                        # Attempt to delete the orphaned file if DB save fails
                        file_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], 'invoices', saved_filename)
                        if os.path.exists(file_to_delete):
                            try:
                                os.remove(file_to_delete)
                            except OSError as os_err:
                                current_app.logger.error(f"Error deleting invoice file {file_to_delete} after DB error: {os_err}")
                # else:
                #     # Added this to handle if save_file itself fails
                #     flash('There was an error processing the uploaded file.', 'error')

    # Fetch recent invoices for history
    recent_invoices = Invoice.query.filter_by(user_id=user.id).order_by(Invoice.submission_date.desc()).limit(5).all()
    return render_template('upload-invoices.html', form=form, invoices=recent_invoices, is_registered=is_registered)


##
@main_bp.route('/all-invoices')
@login_required
@user_required
def all_invoices():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '').strip()
    invoices_query = Invoice.query.filter_by(user_id=g.user.id)

    if query:
        safe_query = query.replace('%', '\\%').replace('_', '\\_')
        search_term = f"%{safe_query}%"
        invoices_query = invoices_query.filter(
            or_(
                Invoice.invoice_number.ilike(search_term, escape='\\'),
                Invoice.po_number.ilike(search_term, escape='\\')
            )
        )

    invoices_pagination = invoices_query.order_by(Invoice.submission_date.desc()).paginate(
        page=page,
        per_page=current_app.config.get('ITEMS_PER_PAGE', 10),
        error_out=False
    )
    return render_template('all_invoices.html', invoices=invoices_pagination, q=query)


def _clean_up_files(filenames, subfolder):
    """Helper to delete files on DB error."""
    for filename in filenames:
        if filename:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError as os_err:
                    current_app.logger.error(f"Error deleting vendor doc {filepath} after DB error: {os_err}")

def _save_material_form(form, user_id):
    """
    [HELPER] Processes file saving and DB creation for Material Vendor.
    Returns True on success, False on failure.
    """
    pan_card_filename = save_file(form.pan_card_copy.data, 'vendor_docs')
    gst_cert_filename = save_file(form.gst_certificate_copy.data, 'vendor_docs')
    cheque_filename = save_file(form.cancelled_cheque_copy.data, 'vendor_docs')
    address_proof_filename = save_file(form.address_proof_copy.data, 'vendor_docs')
    auth_letter_filename = save_file(form.auth_letter_copy.data, 'vendor_docs')

    all_filenames = [pan_card_filename, gst_cert_filename, cheque_filename, address_proof_filename, auth_letter_filename]

    if not all([pan_card_filename, gst_cert_filename, cheque_filename, address_proof_filename]):
         flash('Mandatory file upload failed. Please check errors and retry.', 'error')
         _clean_up_files(all_filenames, 'vendor_docs')
         return False

    try:
        new_vendor_form = VendorMaterial(
            user_id=user_id,
            vendor_name=form.vendor_name.data,
            firm_type=form.firm_type.data,
            firm_type_other=form.firm_type_other.data if form.firm_type.data == 'others' else None,
            nature_of_business=form.nature_of_business.data,
            material_supplied=form.material_supplied.data,
            establishment_date=form.establishment_date.data,
            pan_number=form.pan_number.data.upper(),
            gst_number=form.gst_number.data.upper(),
            office_address_1=form.office_address_1.data, 
            office_address_2=form.office_address_2.data,
            office_city=form.office_city.data, 
            office_state=form.office_state.data, 
            office_pincode=form.office_pincode.data,
            office_contact_person=form.office_contact_person.data, 
            office_mobile=form.office_mobile.data, 
            office_email=form.office_email.data,
            gst_address_1=form.gst_address_1.data, 
            gst_address_2=form.gst_address_2.data,
            gst_city=form.gst_city.data, 
            gst_state=form.gst_state.data, 
            gst_pincode=form.gst_pincode.data,
            gst_contact_person=form.gst_contact_person.data, 
            gst_mobile=form.gst_mobile.data, 
            gst_email=form.gst_email.data,
            account_holder_name=form.account_holder_name.data, 
            bank_name=form.bank_name.data, 
            branch_name=form.branch_name.data,
            account_number=form.account_number.data, 
            ifsc_code=form.ifsc_code.data.upper(),
            primary_contact_name=form.primary_contact_name.data, 
            primary_contact_designation=form.primary_contact_designation.data,
            primary_contact_mobile=form.primary_contact_mobile.data, 
            primary_contact_email=form.primary_contact_email.data,
            alternate_contact_name=form.alternate_contact_name.data, 
            alternate_contact_designation=form.alternate_contact_designation.data,
            alternate_contact_mobile=form.alternate_contact_mobile.data, 
            alternate_contact_email=form.alternate_contact_email.data,
            work_category=json.dumps(form.work_category.data) if form.work_category.data else None,
            work_category_other=form.work_category_other.data if 'other' in (form.work_category.data or []) else None,
            pan_card_copy_path=pan_card_filename,
            gst_certificate_copy_path=gst_cert_filename,
            cancelled_cheque_copy_path=cheque_filename,
            address_proof_copy_path=address_proof_filename,
            auth_letter_copy_path=auth_letter_filename,
            declaration_agreed=form.declaration_agreed.data,
            signature_name=form.signature_name.data,
            signature_date=form.signature_date.data,
            status='Under Review'
        )
        db.session.add(new_vendor_form)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving Material Vendor form for user {user_id}: {e}\n{traceback.format_exc()}")
        flash('An error occurred while submitting the form. Please check your inputs and try again.', 'error')
        _clean_up_files(all_filenames, 'vendor_docs')
        return False

def _save_work_form(form, user_id):
    """
    [HELPER] Processes file saving and DB creation for Work Vendor.
    Returns True on success, False on failure.
    """
    pan_filename = save_file(form.pan_card_copy.data, 'vendor_docs')
    prop_id_filename = save_file(form.proprietor_id_copy.data, 'vendor_docs')
    cheque_filename = save_file(form.cancelled_cheque_copy.data, 'vendor_docs')
    addr_proof_filename = save_file(form.address_proof_copy.data, 'vendor_docs')
    gst_filename = save_file(form.gst_certificate_copy.data, 'vendor_docs')
    pf_esic_filename = save_file(form.pf_esic_copy.data, 'vendor_docs')
    work_orders_filename = save_file(form.work_orders_copy.data, 'vendor_docs')

    all_filenames = [pan_filename, prop_id_filename, cheque_filename, addr_proof_filename, gst_filename, pf_esic_filename, work_orders_filename]

    if not all([pan_filename, prop_id_filename, cheque_filename, addr_proof_filename]):
        flash('Mandatory file upload failed. Please check errors and retry.', 'error')
        _clean_up_files(all_filenames, 'vendor_docs')
        return False

    try:
        new_vendor_form = VendorWork(
            user_id=user_id,
            contractor_name=form.contractor_name.data,
            firm_type=form.firm_type.data,
            firm_type_other=form.firm_type_other.data if form.firm_type.data == 'others' else None,
            scope_of_work=form.scope_of_work.data,
            nature_of_service=form.nature_of_service.data,
            establishment_date=form.establishment_date.data,
            pan_number=form.pan_number.data.upper(),
            gst_number=form.gst_number.data.upper() if form.gst_number.data else None,
            pf_esic_registered=form.pf_esic_registered.data,
            pf_number=form.pf_number.data if form.pf_esic_registered.data == 'Yes' else None,
            esic_number=form.esic_number.data if form.pf_esic_registered.data == 'Yes' else None,
            office_address_1=form.office_address_1.data, 
            office_address_2=form.office_address_2.data,
            office_city=form.office_city.data, 
            office_state=form.office_state.data, 
            office_pincode=form.office_pincode.data,
            office_contact_person=form.office_contact_person.data, 
            office_mobile=form.office_mobile.data, 
            office_email=form.office_email.data,
            site_address_1=form.site_address_1.data, 
            site_address_2=form.site_address_2.data,
            site_city=form.site_city.data, 
            site_state=form.site_state.data, 
            site_pincode=form.site_pincode.data,
            site_contact_person=form.site_contact_person.data, 
            site_mobile=form.site_mobile.data, 
            site_email=form.site_email.data,
            account_holder_name=form.account_holder_name.data, 
            bank_name=form.bank_name.data, 
            branch_name=form.branch_name.data,
            account_number=form.account_number.data, 
            ifsc_code=form.ifsc_code.data.upper(),
            skilled_labour_count=form.skilled_labour_count.data,
            unskilled_labour_count=form.unskilled_labour_count.data,
            supervisor_count=form.supervisor_count.data,
            safety_officer=form.safety_officer.data,
            gst_on_labour=form.gst_on_labour.data,
            work_category=json.dumps(form.work_category.data) if form.work_category.data else None,
            work_category_other=form.work_category_other.data if 'other' in (form.work_category.data or []) else None,
            years_experience=form.years_experience.data,
            major_clients=form.major_clients.data,
            reference_contact=form.reference_contact.data,
            project_experience=form.project_experience.data,
            pan_card_copy_path=pan_filename,
            proprietor_id_copy_path=prop_id_filename,
            cancelled_cheque_copy_path=cheque_filename,
            address_proof_copy_path=addr_proof_filename,
            gst_certificate_copy_path=gst_filename,
            pf_esic_copy_path=pf_esic_filename,
            work_orders_copy_path=work_orders_filename,
            declaration_agreed=form.declaration_agreed.data,
            signature_name=form.signature_name.data,
            signature_date=form.signature_date.data,
            status='Under Review'
        )
        db.session.add(new_vendor_form)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving Work Vendor form for user {user_id}: {e}\n{traceback.format_exc()}")
        flash('An error occurred while submitting the form. Please check your inputs and try again.', 'error')
        _clean_up_files(all_filenames, 'vendor_docs')
        return False


##
@main_bp.route('/vendor-form/material', methods=['GET', 'POST'])
@login_required
@user_required
def vendor_form_material():
    user_id = g.user.id
    if VendorWork.query.filter_by(user_id=user_id).first():
        flash('You have already submitted the Work Vendor form. You can only submit one type of form.', 'warning')
        return redirect(url_for('main.dashboard'))

    existing_form = VendorMaterial.query.filter_by(user_id=user_id).first()
    form_kwargs = {'obj': existing_form} if existing_form else {}
    form = VendorMaterialForm(**form_kwargs)

    if not existing_form and form.validate_on_submit():
        if _save_material_form(form, user_id):
            flash('Material Vendor form submitted successfully! Your application is under review.', 'success')
            return redirect(url_for('main.dashboard'))

    if existing_form and existing_form.work_category:
        try:
            form.work_category.data = json.loads(existing_form.work_category)
        except json.JSONDecodeError:
            form.work_category.data = []

    return render_template('vendor-form-material.html', form=form, existing_form=existing_form)


##
@main_bp.route('/vendor-form/work', methods=['GET', 'POST'])
@login_required
@user_required
def vendor_form_work():
    user_id = g.user.id
    if VendorMaterial.query.filter_by(user_id=user_id).first():
        flash('You have already submitted the Material Vendor form. You can only submit one type of form.', 'warning')
        return redirect(url_for('main.dashboard'))

    existing_form = VendorWork.query.filter_by(user_id=user_id).first()
    form_kwargs = {'obj': existing_form} if existing_form else {}
    form = VendorWorkForm(**form_kwargs)

    if not existing_form and form.validate_on_submit():
        if _save_work_form(form, user_id):
            flash('Work Vendor form submitted successfully! Your application is under review.', 'success')
            return redirect(url_for('main.dashboard'))

    if existing_form and existing_form.work_category:
        try:
            form.work_category.data = json.loads(existing_form.work_category)
        except json.JSONDecodeError:
            form.work_category.data = []

    return render_template('vendor-form-work.html', form=form, existing_form=existing_form)


##
@main_bp.route('/help-support', methods=['GET', 'POST'])
@login_required
@user_required
def help_support():
    user = g.user
    form = SupportTicketForm()

    if form.validate_on_submit():
        try:
            pan_last_three = user.pan_number[-3:] if user.pan_number else "XXXX"
            random_part = str(secrets.randbelow(900000) + 100000)
            ticket_id = f"TKT-{pan_last_three}-{random_part}"
            
            
            if SupportTicket.query.get(ticket_id):
                random_part = str(secrets.randbelow(900000) + 100000)
                ticket_id = f"TKT-{pan_last_three}-{random_part}"

            new_ticket = SupportTicket(
                id=ticket_id,
                user_id=user.id,
                category=form.category.data,
                invoice_no=form.invoice_no.data if form.category.data in ['Payment Query', 'Invoice Rejection'] else None,
                subject=form.subject.data,
                message=form.message.data,
                status=TicketStatus.OPEN,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_ticket)
            db.session.commit()
            flash(f'Support ticket {ticket_id} submitted successfully!', 'success')
            return redirect(url_for('main.help_support'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving support ticket for user {user.id}: {e}\n{traceback.format_exc()}")
            flash('An error occurred while submitting the ticket. Please try again.', 'error')

    tickets = SupportTicket.query.filter_by(user_id=user.id).order_by(SupportTicket.created_at.desc()).all()
    return render_template('help-support.html', form=form, tickets=tickets, TicketStatus=TicketStatus)


# --- File Download Routes ---
# The logic to check if the file exists AND belongs to the logged-in user
# (or an admin) is the correct way to prevent Insecure Direct Object Reference (IDOR).
@main_bp.route('/download/vendor_doc/<path:filename>')
@user_or_admin_required
def download_vendor_doc(filename):
    """
    Securely serves files from the 'vendor_docs' subfolder
    after verifying ownership (or if admin).
    """
    user_id = session.get('user_id')
    is_admin = 'admin_id' in session

    # Sanitize filename (good)
    filename = secure_filename(filename)
    if not filename:
        flash('Invalid filename.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], 'vendor_docs')
    
    if not is_admin:
        owns_material_file = VendorMaterial.query.filter_by(user_id=user_id).filter(
            or_(
                VendorMaterial.pan_card_copy_path == filename,
                VendorMaterial.gst_certificate_copy_path == filename,
                VendorMaterial.cancelled_cheque_copy_path == filename,
                VendorMaterial.address_proof_copy_path == filename,
                VendorMaterial.auth_letter_copy_path == filename
            )
        ).first()
        owns_work_file = VendorWork.query.filter_by(user_id=user_id).filter(
            or_(
                VendorWork.pan_card_copy_path == filename,
                VendorWork.proprietor_id_copy_path == filename,
                VendorWork.cancelled_cheque_copy_path == filename,
                VendorWork.address_proof_copy_path == filename,
                VendorWork.gst_certificate_copy_path == filename,
                VendorWork.pf_esic_copy_path == filename,
                VendorWork.work_orders_copy_path == filename
            )
        ).first()

        if not owns_material_file and not owns_work_file:
            flash('You do not have permission to access this file.', 'error')
            return redirect(url_for('main.dashboard'))
    
    file_path = os.path.join(directory, filename)
    if not os.path.isfile(file_path):
        flash('File not found.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    try:
        return send_from_directory(directory, filename, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"Error serving vendor doc {filename}: {e}")
        flash('An error occurred while accessing the file.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/download/invoice/<path:filename>')
@user_or_admin_required
def download_invoice(filename):
    """
    Securely serves files from the 'invoices' subfolder
    after verifying ownership (or if admin).
    """
    user_id = session.get('user_id')
    is_admin = 'admin_id' in session

    filename = secure_filename(filename)
    if not filename:
        flash('Invalid filename.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], 'invoices')

    if not is_admin:
        invoice = Invoice.query.filter_by(user_id=user_id, file_path=filename).first()
        if not invoice:
            flash('You do not have permission to access this file.', 'error')
            return redirect(url_for('main.dashboard'))
    
    file_path = os.path.join(directory, filename)
    if not os.path.isfile(file_path):
        flash('File not found.', 'error')
        return redirect(request.referrer or url_for('main.dashboard'))

    try:
        return send_from_directory(directory, filename, as_attachment=False)
    except Exception as e:
         current_app.logger.error(f"Error serving invoice file {filename}: {e}")
         flash('An error occurred while accessing the file.', 'error')
         return redirect(request.referrer or url_for('main.dashboard'))


## --- Error handlers ---
@main_bp.app_errorhandler(404)
def page_not_found(e):
    """
    Handles 404 'Not Found' errors for the entire application.
    """
    current_app.logger.warning(f"404 Not Found: {request.path} (Referrer: {request.referrer})")
    return render_template('error/404.html'), 404


@main_bp.app_errorhandler(Exception)
def internal_server_error(e):
    """
    Handles 500 'Internal Server Error' (all unhandled exceptions)
    for the entire application.
    """
    # Log the full exception and stack trace
    error_trace = traceback.format_exc()
    current_app.logger.error(f"500 Internal Server Error: {e}\n{error_trace}")
    
    # It's crucial to roll back the database session
    # in case the error was caused by a failed DB operation.
    try:
        db.session.rollback()
        current_app.logger.info("Database session rolled back after error.")
    except Exception as rb_e:
        current_app.logger.error(f"CRITICAL: Failed to rollback session after error: {rb_e}")

    return render_template('error/500.html'), 500




#
#
#
#
# --- Placeholder routes ---
@main_bp.route('/messages')
@login_required
def messages():
    return render_template('messages.html')


@main_bp.route('/notifications')
@login_required
def notifications():
    # This is fine as a placeholder.
    # For deployment, you'd replace this with a real DB query.
    dummy_notifications = [
         {'id': 1, 'message': 'Invoice INV-2025-071 has been Approved.', 'timestamp': datetime(2025, 10, 29, 10, 30), 'is_read': False, 'category': 'success', 'link_url': url_for('main.all_invoices')},
         {'id': 2, 'message': 'Payment for INV-2025-065 has been processed.', 'timestamp': datetime(2025, 10, 28, 15, 0), 'is_read': False, 'category': 'success', 'link_url': '#'},
         {'id': 3, 'message': 'Invoice INV-2025-070 was Rejected. Reason: Incorrect PO number.', 'timestamp': datetime(2025, 10, 27, 9, 15), 'is_read': True, 'category': 'error', 'link_url': url_for('main.all_invoices')},
         {'id': 4, 'message': 'Reminder: Please update your bank details if they have changed.', 'timestamp': datetime(2025, 10, 25, 11, 0), 'is_read': True, 'category': 'info', 'link_url': url_for('main.your_profile')},
    ]
    return render_template('notifications.html', notifications=dummy_notifications)


# --- Payment History Route ---
@main_bp.route('/payment-history')
@login_required
@user_required # --- [NEW] Loads g.user
def payment_history():
    page = request.args.get('page', 1, type=int)
    paid_invoices_query = Invoice.query.filter_by(user_id=g.user.id, status='Paid')

    paid_invoices_pagination = paid_invoices_query.order_by(
        Invoice.payment_date.desc().nullslast(),
        Invoice.submission_date.desc()
        ).paginate(
            page=page,
            per_page=current_app.config.get('ITEMS_PER_PAGE', 15),
            error_out=False
        )

    return render_template('all_invoices.html',
                           invoices=paid_invoices_pagination,
                           page_title="Payment History", # This is a good way to reuse the template
                           q=request.args.get('q', ''))
