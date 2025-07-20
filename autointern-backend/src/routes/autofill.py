from flask import Blueprint, request, jsonify, current_app
import json
import requests
from datetime import datetime
from src.models.user_enhanced import db, User, UserProfile, CVData, Internship, Application
from src.routes.auth_enhanced_github import verify_token
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

autofill_bp = Blueprint('autofill', __name__)

def get_user_from_token(request):
    """Extract user from JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    
    if not user_id:
        return None
    
    return User.query.get(user_id)

def setup_chrome_driver():
    """Setup Chrome driver for web automation"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

@autofill_bp.route('/autofill/profile', methods=['GET'])
def get_autofill_profile():
    """Get user's autofill profile data"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        autofill_data = {
            'personal_info': {
                'full_name': user.name or '',
                'first_name': profile.first_name or '' if profile else '',
                'last_name': profile.last_name or '' if profile else '',
                'email': user.email or '',
                'phone': profile.phone or '' if profile else '',
                'linkedin_url': profile.linkedin_url or '' if profile else '',
                'github_url': profile.github_url or '' if profile else '',
                'portfolio_url': profile.portfolio_url or '' if profile else ''
            },
            'professional_info': {
                'skills': profile.skills or '' if profile else '',
                'education': profile.education or '' if profile else '',
                'experience': profile.experience or '' if profile else '',
                'bio': profile.bio or '' if profile else ''
            },
            'cv_data': cv_data.to_dict() if cv_data else None
        }
        
        return jsonify(autofill_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@autofill_bp.route('/autofill/profile', methods=['PUT'])
def update_autofill_profile():
    """Update user's autofill profile data"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        personal_info = data.get('personal_info', {})
        professional_info = data.get('professional_info', {})
        
        # Update user info
        if personal_info.get('full_name'):
            user.name = personal_info['full_name']
        
        # Get or create profile
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
        
        # Update profile info
        profile.first_name = personal_info.get('first_name', profile.first_name)
        profile.last_name = personal_info.get('last_name', profile.last_name)
        profile.phone = personal_info.get('phone', profile.phone)
        profile.linkedin_url = personal_info.get('linkedin_url', profile.linkedin_url)
        profile.github_url = personal_info.get('github_url', profile.github_url)
        profile.portfolio_url = personal_info.get('portfolio_url', profile.portfolio_url)
        profile.skills = professional_info.get('skills', profile.skills)
        profile.education = professional_info.get('education', profile.education)
        profile.experience = professional_info.get('experience', profile.experience)
        profile.bio = professional_info.get('bio', profile.bio)
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@autofill_bp.route('/autofill/detect-fields', methods=['POST'])
def detect_form_fields():
    """Detect form fields on a webpage for autofill"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        driver = setup_chrome_driver()
        if not driver:
            return jsonify({'error': 'Failed to setup web driver'}), 500
        
        try:
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Common field selectors and their types
            field_mappings = {
                'name': ['input[name*="name"]', 'input[id*="name"]', 'input[placeholder*="name"]'],
                'first_name': ['input[name*="first"]', 'input[id*="first"]', 'input[placeholder*="first"]'],
                'last_name': ['input[name*="last"]', 'input[id*="last"]', 'input[placeholder*="last"]'],
                'email': ['input[type="email"]', 'input[name*="email"]', 'input[id*="email"]'],
                'phone': ['input[type="tel"]', 'input[name*="phone"]', 'input[id*="phone"]'],
                'linkedin': ['input[name*="linkedin"]', 'input[id*="linkedin"]', 'input[placeholder*="linkedin"]'],
                'github': ['input[name*="github"]', 'input[id*="github"]', 'input[placeholder*="github"]'],
                'portfolio': ['input[name*="portfolio"]', 'input[id*="portfolio"]', 'input[name*="website"]'],
                'cover_letter': ['textarea[name*="cover"]', 'textarea[id*="cover"]', 'textarea[name*="letter"]'],
                'resume': ['input[type="file"]', 'input[name*="resume"]', 'input[name*="cv"]']
            }
            
            detected_fields = {}
            
            for field_type, selectors in field_mappings.items():
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            element = elements[0]
                            detected_fields[field_type] = {
                                'selector': selector,
                                'tag': element.tag_name,
                                'type': element.get_attribute('type'),
                                'name': element.get_attribute('name'),
                                'id': element.get_attribute('id'),
                                'placeholder': element.get_attribute('placeholder')
                            }
                            break
                    except Exception:
                        continue
            
            return jsonify({
                'url': url,
                'detected_fields': detected_fields,
                'total_fields': len(detected_fields)
            }), 200
            
        finally:
            driver.quit()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@autofill_bp.route('/autofill/fill-form', methods=['POST'])
def autofill_form():
    """Automatically fill a job application form"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        url = data.get('url')
        field_mappings = data.get('field_mappings', {})
        custom_data = data.get('custom_data', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Get user profile data
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        
        # Prepare autofill data
        fill_data = {
            'name': user.name or '',
            'first_name': profile.first_name or '' if profile else '',
            'last_name': profile.last_name or '' if profile else '',
            'email': user.email or '',
            'phone': profile.phone or '' if profile else '',
            'linkedin': profile.linkedin_url or '' if profile else '',
            'github': profile.github_url or '' if profile else '',
            'portfolio': profile.portfolio_url or '' if profile else '',
            'cover_letter': custom_data.get('cover_letter', ''),
            **custom_data
        }
        
        driver = setup_chrome_driver()
        if not driver:
            return jsonify({'error': 'Failed to setup web driver'}), 500
        
        try:
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            filled_fields = []
            errors = []
            
            for field_type, field_info in field_mappings.items():
                if field_type in fill_data and fill_data[field_type]:
                    try:
                        selector = field_info.get('selector')
                        if selector:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                            
                            # Clear existing content
                            element.clear()
                            
                            # Fill with data
                            if element.tag_name.lower() == 'textarea':
                                element.send_keys(fill_data[field_type])
                            elif element.get_attribute('type') == 'file':
                                # Handle file upload (resume/CV)
                                if field_type == 'resume' and custom_data.get('resume_path'):
                                    element.send_keys(custom_data['resume_path'])
                            else:
                                element.send_keys(fill_data[field_type])
                            
                            filled_fields.append({
                                'field': field_type,
                                'value': fill_data[field_type][:50] + '...' if len(fill_data[field_type]) > 50 else fill_data[field_type],
                                'selector': selector
                            })
                            
                    except Exception as e:
                        errors.append({
                            'field': field_type,
                            'error': str(e)
                        })
            
            # Take screenshot for verification
            screenshot_path = f"/tmp/autofill_screenshot_{user.id}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            
            return jsonify({
                'success': True,
                'filled_fields': filled_fields,
                'errors': errors,
                'screenshot_path': screenshot_path,
                'message': f'Successfully filled {len(filled_fields)} fields'
            }), 200
            
        finally:
            driver.quit()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@autofill_bp.route('/autofill/submit-application', methods=['POST'])
def submit_application():
    """Submit a job application after autofill"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        url = data.get('url')
        internship_id = data.get('internship_id')
        submit_selector = data.get('submit_selector', 'input[type="submit"], button[type="submit"], button:contains("Submit")')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        driver = setup_chrome_driver()
        if not driver:
            return jsonify({'error': 'Failed to setup web driver'}), 500
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Find and click submit button
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector))
                )
                submit_button.click()
                
                # Wait for submission to complete
                time.sleep(5)
                
                # Check for success indicators
                success_indicators = [
                    'thank you', 'success', 'submitted', 'received',
                    'شكرا', 'نجح', 'تم الإرسال', 'تم الاستلام'
                ]
                
                page_text = driver.page_source.lower()
                submission_successful = any(indicator in page_text for indicator in success_indicators)
                
                # Record application in database
                if internship_id and submission_successful:
                    internship = Internship.query.get(internship_id)
                    if internship:
                        application = Application(
                            user_id=user.id,
                            internship_id=internship_id,
                            status='submitted',
                            auto_applied=True,
                            applied_date=datetime.utcnow()
                        )
                        db.session.add(application)
                        db.session.commit()
                
                return jsonify({
                    'success': submission_successful,
                    'message': 'Application submitted successfully' if submission_successful else 'Submission status unclear',
                    'current_url': driver.current_url
                }), 200
                
            except TimeoutException:
                return jsonify({
                    'success': False,
                    'error': 'Submit button not found or not clickable'
                }), 400
                
        finally:
            driver.quit()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@autofill_bp.route('/autofill/templates', methods=['GET'])
def get_autofill_templates():
    """Get predefined autofill templates for common job sites"""
    templates = {
        'linkedin': {
            'name': 'LinkedIn Jobs',
            'url_pattern': 'linkedin.com/jobs',
            'field_mappings': {
                'cover_letter': {'selector': 'textarea[name="coverLetter"]'},
                'resume': {'selector': 'input[type="file"]'}
            }
        },
        'indeed': {
            'name': 'Indeed',
            'url_pattern': 'indeed.com',
            'field_mappings': {
                'name': {'selector': 'input[name="applicant.name"]'},
                'email': {'selector': 'input[name="applicant.emailAddress"]'},
                'phone': {'selector': 'input[name="applicant.phoneNumber"]'},
                'cover_letter': {'selector': 'textarea[name="coverletter"]'}
            }
        },
        'glassdoor': {
            'name': 'Glassdoor',
            'url_pattern': 'glassdoor.com',
            'field_mappings': {
                'first_name': {'selector': 'input[name="firstName"]'},
                'last_name': {'selector': 'input[name="lastName"]'},
                'email': {'selector': 'input[name="email"]'},
                'phone': {'selector': 'input[name="phone"]'}
            }
        },
        'generic': {
            'name': 'Generic Form',
            'url_pattern': '*',
            'field_mappings': {
                'name': {'selector': 'input[name*="name"], input[id*="name"]'},
                'email': {'selector': 'input[type="email"], input[name*="email"]'},
                'phone': {'selector': 'input[type="tel"], input[name*="phone"]'},
                'cover_letter': {'selector': 'textarea[name*="cover"], textarea[id*="cover"]'}
            }
        }
    }
    
    return jsonify({'templates': templates}), 200

@autofill_bp.route('/autofill/history', methods=['GET'])
def get_autofill_history():
    """Get user's autofill history"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get auto-applied applications
        applications = Application.query.filter_by(
            user_id=user.id,
            auto_applied=True
        ).order_by(Application.applied_date.desc()).all()
        
        history = []
        for app in applications:
            history.append({
                'id': app.id,
                'internship': app.internship.to_dict() if app.internship else None,
                'applied_date': app.applied_date.isoformat() if app.applied_date else None,
                'status': app.status,
                'ai_generated_cover_letter': app.ai_generated_cover_letter
            })
        
        return jsonify({
            'history': history,
            'total_auto_applications': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

