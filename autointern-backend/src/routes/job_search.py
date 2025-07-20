from flask import Blueprint, request, jsonify, current_app
import requests
from bs4 import BeautifulSoup
import json
import openai
from datetime import datetime, timedelta
from src.models.user_enhanced import db, User, UserProfile, CVData, Internship, Application, ApplicationTracking
from src.routes.auth_enhanced_github import verify_token
from src.routes.ai_chatbot import get_user_from_token
import re
import time
from urllib.parse import urljoin, urlparse

job_search_bp = Blueprint('job_search', __name__)

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def extract_keywords_from_text(text):
    """Extract keywords from job description or CV text"""
    if not text:
        return []
    
    # Common tech keywords and skills
    tech_keywords = [
        'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'html', 'css',
        'machine learning', 'data science', 'artificial intelligence', 'ai',
        'web development', 'mobile development', 'frontend', 'backend', 'fullstack',
        'database', 'api', 'rest', 'graphql', 'docker', 'kubernetes', 'aws', 'azure',
        'git', 'github', 'agile', 'scrum', 'testing', 'debugging'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in tech_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords

@job_search_bp.route('/jobs/search', methods=['POST'])
def search_jobs():
    """Search for jobs based on user criteria"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        location = data.get('location', '')
        job_type = data.get('job_type', 'internship')
        experience_level = data.get('experience_level', 'entry')
        language = data.get('language', 'en')
        
        # Get user's CV data for better matching
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        user_skills = []
        if cv_data and cv_data.skills:
            try:
                user_skills = json.loads(cv_data.skills)
            except:
                user_skills = cv_data.skills.split(',') if cv_data.skills else []
        
        # Combine user skills with search keywords
        all_keywords = list(set(keywords + user_skills))
        
        # Search multiple job sites
        job_results = []
        
        # Search LinkedIn (simulated - in real implementation, you'd use LinkedIn API)
        linkedin_jobs = search_linkedin_jobs(all_keywords, location, job_type)
        job_results.extend(linkedin_jobs)
        
        # Search Indeed (simulated)
        indeed_jobs = search_indeed_jobs(all_keywords, location, job_type)
        job_results.extend(indeed_jobs)
        
        # Search company websites (simulated)
        company_jobs = search_company_websites(all_keywords, location)
        job_results.extend(company_jobs)
        
        # Save new jobs to database
        saved_jobs = []
        for job in job_results:
            existing_job = Internship.query.filter_by(
                title=job['title'],
                company=job['company']
            ).first()
            
            if not existing_job:
                new_job = Internship(
                    title=job['title'],
                    company=job['company'],
                    location=job['location'],
                    description=job['description'],
                    url=job['url'],
                    requirements=job.get('requirements', ''),
                    source='scraped',
                    keywords=json.dumps(job.get('keywords', []))
                )
                db.session.add(new_job)
                saved_jobs.append(new_job)
        
        db.session.commit()
        
        return jsonify({
            'jobs': [job for job in job_results],
            'total_found': len(job_results),
            'new_jobs_saved': len(saved_jobs),
            'search_criteria': {
                'keywords': all_keywords,
                'location': location,
                'job_type': job_type
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def search_linkedin_jobs(keywords, location, job_type):
    """Simulate LinkedIn job search (replace with actual API calls)"""
    # In a real implementation, you would use LinkedIn's API or web scraping
    # This is a simulation with sample data
    sample_jobs = [
        {
            'title': 'Software Engineering Intern',
            'company': 'Tech Corp',
            'location': location or 'Remote',
            'description': f'Looking for a {job_type} with skills in {", ".join(keywords[:3])}. Great opportunity to learn and grow.',
            'url': 'https://linkedin.com/jobs/sample1',
            'requirements': 'Basic programming knowledge, eager to learn',
            'keywords': keywords[:3],
            'source': 'linkedin'
        },
        {
            'title': 'Data Science Intern',
            'company': 'Data Solutions Inc',
            'location': location or 'New York',
            'description': f'Data science internship focusing on {", ".join(keywords[:2])} and analytics.',
            'url': 'https://linkedin.com/jobs/sample2',
            'requirements': 'Python, statistics, machine learning basics',
            'keywords': ['python', 'data science', 'machine learning'],
            'source': 'linkedin'
        }
    ]
    return sample_jobs

def search_indeed_jobs(keywords, location, job_type):
    """Simulate Indeed job search"""
    sample_jobs = [
        {
            'title': 'Web Development Intern',
            'company': 'StartupXYZ',
            'location': location or 'San Francisco',
            'description': f'Web development {job_type} working with {", ".join(keywords[:2])} technologies.',
            'url': 'https://indeed.com/jobs/sample1',
            'requirements': 'HTML, CSS, JavaScript knowledge',
            'keywords': ['javascript', 'html', 'css', 'web development'],
            'source': 'indeed'
        }
    ]
    return sample_jobs

def search_company_websites(keywords, location):
    """Simulate company website job search"""
    sample_jobs = [
        {
            'title': 'Mobile App Development Intern',
            'company': 'Mobile Innovations',
            'location': location or 'Austin',
            'description': f'Mobile app development internship with focus on {", ".join(keywords[:2])}.',
            'url': 'https://company.com/careers/intern1',
            'requirements': 'Mobile development experience preferred',
            'keywords': ['mobile development', 'react native', 'flutter'],
            'source': 'company_website'
        }
    ]
    return sample_jobs

@job_search_bp.route('/jobs/auto-apply', methods=['POST'])
def auto_apply_jobs():
    """Automatically apply to jobs based on user preferences"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        auto_generate_cover_letter = data.get('auto_generate_cover_letter', True)
        language = data.get('language', 'en')
        
        if not job_ids:
            return jsonify({'error': 'Job IDs are required'}), 400
        
        # Get user profile for cover letter generation
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        user_skills = profile.skills if profile else ''
        user_experience = profile.experience if profile else ''
        
        applied_jobs = []
        failed_applications = []
        
        for job_id in job_ids:
            try:
                job = Internship.query.get(job_id)
                if not job:
                    failed_applications.append({
                        'job_id': job_id,
                        'error': 'Job not found'
                    })
                    continue
                
                # Check if already applied
                existing_application = Application.query.filter_by(
                    user_id=user.id,
                    internship_id=job_id
                ).first()
                
                if existing_application:
                    failed_applications.append({
                        'job_id': job_id,
                        'error': 'Already applied to this job'
                    })
                    continue
                
                # Generate cover letter if requested
                cover_letter = ''
                ai_generated = False
                
                if auto_generate_cover_letter:
                    try:
                        if language == 'ar':
                            prompt = f"""اكتب رسالة تغطية مهنية باللغة العربية للوظيفة التالية:

المسمى الوظيفي: {job.title}
اسم الشركة: {job.company}
وصف الوظيفة: {job.description}

معلومات المتقدم:
المهارات: {user_skills}
الخبرة: {user_experience}

يرجى كتابة رسالة تغطية مختصرة ومهنية."""
                        else:
                            prompt = f"""Write a professional cover letter for the following job:

Job Title: {job.title}
Company: {job.company}
Job Description: {job.description}

Applicant Information:
Skills: {user_skills}
Experience: {user_experience}

Please write a concise and professional cover letter."""
                        
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a professional career advisor."},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=800,
                            temperature=0.7
                        )
                        
                        cover_letter = response.choices[0].message.content
                        ai_generated = True
                        
                    except Exception as e:
                        # Use default cover letter if AI fails
                        if language == 'ar':
                            cover_letter = f"عزيزي فريق التوظيف في {job.company}،\n\nأتقدم بطلب للحصول على منصب {job.title}. أعتقد أن مهاراتي وخبرتي تجعلني مرشحاً مناسباً لهذا المنصب.\n\nأتطلع إلى سماع ردكم.\n\nمع أطيب التحيات"
                        else:
                            cover_letter = f"Dear {job.company} Hiring Team,\n\nI am writing to apply for the {job.title} position. I believe my skills and experience make me a suitable candidate for this role.\n\nI look forward to hearing from you.\n\nBest regards"
                
                # Create application record
                application = Application(
                    user_id=user.id,
                    internship_id=job_id,
                    status='submitted',
                    cover_letter=cover_letter,
                    auto_applied=True,
                    ai_generated_cover_letter=ai_generated,
                    applied_date=datetime.utcnow()
                )
                
                db.session.add(application)
                
                # Add tracking record
                tracking = ApplicationTracking(
                    application_id=application.id,
                    status='submitted',
                    notes='Auto-applied via system',
                    changed_by=user.id,
                    changed_at=datetime.utcnow()
                )
                
                db.session.add(tracking)
                
                applied_jobs.append({
                    'job_id': job_id,
                    'job_title': job.title,
                    'company': job.company,
                    'application_id': application.id,
                    'ai_generated_cover_letter': ai_generated
                })
                
            except Exception as e:
                failed_applications.append({
                    'job_id': job_id,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'applied_jobs': applied_jobs,
            'failed_applications': failed_applications,
            'total_applied': len(applied_jobs),
            'total_failed': len(failed_applications)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_search_bp.route('/applications/tracker', methods=['GET'])
def get_application_tracker():
    """Get user's application tracking dashboard"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get all user applications with tracking
        applications = Application.query.filter_by(user_id=user.id).order_by(
            Application.applied_date.desc()
        ).all()
        
        # Group by status
        status_counts = {}
        applications_by_status = {}
        
        for app in applications:
            status = app.status
            if status not in status_counts:
                status_counts[status] = 0
                applications_by_status[status] = []
            
            status_counts[status] += 1
            applications_by_status[status].append(app.to_dict())
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_applications = [
            app for app in applications 
            if app.applied_date and app.applied_date >= thirty_days_ago
        ]
        
        # Calculate success rate (accepted / total)
        total_apps = len(applications)
        accepted_apps = status_counts.get('accepted', 0)
        success_rate = (accepted_apps / total_apps * 100) if total_apps > 0 else 0
        
        return jsonify({
            'summary': {
                'total_applications': total_apps,
                'status_counts': status_counts,
                'success_rate': round(success_rate, 2),
                'recent_applications': len(recent_applications)
            },
            'applications_by_status': applications_by_status,
            'recent_activity': [app.to_dict() for app in recent_applications[:10]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@job_search_bp.route('/applications/<int:application_id>/status', methods=['PUT'])
def update_application_status():
    """Update application status"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Valid statuses
        valid_statuses = [
            'submitted', 'under_review', 'interview_scheduled', 
            'interviewed', 'accepted', 'rejected', 'withdrawn'
        ]
        
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        application = Application.query.filter_by(
            id=application_id,
            user_id=user.id
        ).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Update application status
        old_status = application.status
        application.status = new_status
        application.updated_at = datetime.utcnow()
        
        # Add tracking record
        tracking = ApplicationTracking(
            application_id=application.id,
            status=new_status,
            notes=notes,
            changed_by=user.id,
            changed_at=datetime.utcnow()
        )
        
        db.session.add(tracking)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'application_id': application.id,
            'old_status': old_status,
            'new_status': new_status,
            'updated_at': application.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_search_bp.route('/applications/<int:application_id>/tracking', methods=['GET'])
def get_application_tracking():
    """Get detailed tracking history for an application"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        application = Application.query.filter_by(
            id=application_id,
            user_id=user.id
        ).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Get tracking history
        tracking_history = ApplicationTracking.query.filter_by(
            application_id=application.id
        ).order_by(ApplicationTracking.changed_at.desc()).all()
        
        return jsonify({
            'application': application.to_dict(),
            'tracking_history': [track.to_dict() for track in tracking_history]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@job_search_bp.route('/jobs/recommendations', methods=['GET'])
def get_job_recommendations():
    """Get AI-powered job recommendations for the user"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get user profile and CV data
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        user_skills = []
        if cv_data and cv_data.skills:
            try:
                user_skills = json.loads(cv_data.skills)
            except:
                user_skills = cv_data.skills.split(',') if cv_data.skills else []
        
        # Get available jobs
        available_jobs = Internship.query.limit(50).all()
        
        if not available_jobs:
            return jsonify({
                'recommendations': [],
                'message': 'No jobs available for recommendations'
            }), 200
        
        # Score jobs based on skill matching
        job_scores = []
        
        for job in available_jobs:
            score = 0
            job_keywords = []
            
            if job.keywords:
                try:
                    job_keywords = json.loads(job.keywords)
                except:
                    job_keywords = extract_keywords_from_text(job.description)
            else:
                job_keywords = extract_keywords_from_text(job.description)
            
            # Calculate match score
            matching_skills = set(user_skills).intersection(set(job_keywords))
            score = len(matching_skills) / max(len(job_keywords), 1) * 100
            
            job_scores.append({
                'job': job.to_dict(),
                'score': round(score, 2),
                'matching_skills': list(matching_skills),
                'total_job_keywords': len(job_keywords)
            })
        
        # Sort by score and get top recommendations
        job_scores.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = job_scores[:10]
        
        return jsonify({
            'recommendations': top_recommendations,
            'user_skills': user_skills,
            'total_jobs_analyzed': len(available_jobs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

