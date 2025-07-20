from flask import Blueprint, request, jsonify, current_app
import os
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import PyPDF2
import docx
from src.models.user_enhanced import db, User, UserProfile, CVData
from src.routes.auth_enhanced_github import verify_token
import openai
import spacy
from collections import Counter

cv_parser_bp = Blueprint('cv_parser', __name__)

# Load spaCy model for NLP (you might need to install: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

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

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error extracting TXT text: {e}")
        return ""

def extract_text_from_file(file_path):
    """Extract text from various file formats"""
    file_extension = file_path.lower().split('.')[-1]
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension in ['txt', 'doc']:
        return extract_text_from_txt(file_path)
    else:
        return ""

def extract_email(text):
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None

def extract_phone(text):
    """Extract phone numbers from text"""
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
        r'\b[0-9]{10,15}\b'
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0]
    return None

def extract_skills(text):
    """Extract skills from CV text"""
    # Common technical skills
    tech_skills = [
        'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
        'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
        'machine learning', 'deep learning', 'ai', 'data science', 'analytics',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        'project management', 'agile', 'scrum', 'leadership', 'communication'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in tech_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    # Use spaCy for additional skill extraction if available
    if nlp:
        doc = nlp(text)
        # Extract noun phrases that might be skills
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3 and chunk.text.lower() not in found_skills:
                # Simple heuristic: if it contains tech-related words
                tech_indicators = ['development', 'programming', 'software', 'web', 'mobile', 'data']
                if any(indicator in chunk.text.lower() for indicator in tech_indicators):
                    found_skills.append(chunk.text.lower())
    
    return list(set(found_skills))

def extract_experience_years(text):
    """Extract years of experience from CV text"""
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience\s*:?\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*in\s*(?:the\s*)?(?:field|industry)',
    ]
    
    text_lower = text.lower()
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                return int(matches[0])
            except ValueError:
                continue
    
    return 0

def extract_education_level(text):
    """Extract education level from CV text"""
    education_keywords = {
        'phd': ['phd', 'ph.d', 'doctorate', 'doctoral'],
        'masters': ['masters', 'master', 'm.s', 'msc', 'm.sc', 'mba', 'm.a'],
        'bachelors': ['bachelors', 'bachelor', 'b.s', 'bsc', 'b.sc', 'b.a', 'ba', 'bs'],
        'associates': ['associates', 'associate', 'a.s', 'aa'],
        'high_school': ['high school', 'secondary', 'diploma']
    }
    
    text_lower = text.lower()
    
    for level, keywords in education_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return level
    
    return 'unknown'

def extract_job_titles(text):
    """Extract job titles from CV text"""
    # Common job title patterns
    title_patterns = [
        r'(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:at|@|\|)',
        r'(?:position|role|title)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:worked as|served as)\s+(?:a\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    job_titles = []
    
    for pattern in title_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        job_titles.extend(matches)
    
    # Common job titles to look for
    common_titles = [
        'software engineer', 'developer', 'programmer', 'analyst', 'manager',
        'intern', 'associate', 'specialist', 'consultant', 'coordinator',
        'designer', 'architect', 'lead', 'senior', 'junior', 'data scientist'
    ]
    
    text_lower = text.lower()
    for title in common_titles:
        if title in text_lower:
            job_titles.append(title)
    
    return list(set(job_titles))

def extract_keywords_ai(text, language='en'):
    """Use AI to extract keywords from CV"""
    try:
        if language == 'ar':
            prompt = f"""حلل النص التالي من السيرة الذاتية واستخرج الكلمات المفتاحية المهمة:

{text[:2000]}  # Limit text length

يرجى استخراج:
1. المهارات التقنية
2. المهارات الشخصية
3. الكلمات المفتاحية المهنية
4. أسماء التقنيات والأدوات

قدم النتيجة كقائمة مفصولة بفواصل."""
        else:
            prompt = f"""Analyze the following CV text and extract important keywords:

{text[:2000]}  # Limit text length

Please extract:
1. Technical skills
2. Soft skills
3. Professional keywords
4. Technology and tool names

Provide the result as a comma-separated list."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert CV analyzer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content
        keywords = [kw.strip() for kw in keywords_text.split(',')]
        return keywords
        
    except Exception as e:
        print(f"Error extracting keywords with AI: {e}")
        return []

@cv_parser_bp.route('/cv/upload', methods=['POST'])
def upload_cv():
    """Upload and parse CV file"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        language = request.form.get('language', 'en')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', '/tmp'), 'cvs')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"{user.id}_{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Extract text from file
        extracted_text = extract_text_from_file(file_path)
        
        if not extracted_text:
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        # Parse CV data
        email = extract_email(extracted_text)
        phone = extract_phone(extracted_text)
        skills = extract_skills(extracted_text)
        experience_years = extract_experience_years(extracted_text)
        education_level = extract_education_level(extracted_text)
        job_titles = extract_job_titles(extracted_text)
        
        # Extract keywords using AI
        ai_keywords = extract_keywords_ai(extracted_text, language)
        all_keywords = list(set(skills + ai_keywords))
        
        # Save or update CV data
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        if not cv_data:
            cv_data = CVData(user_id=user.id)
            db.session.add(cv_data)
        
        cv_data.file_path = file_path
        cv_data.extracted_text = extracted_text
        cv_data.keywords = json.dumps(all_keywords)
        cv_data.skills = json.dumps(skills)
        cv_data.experience_years = experience_years
        cv_data.education_level = education_level
        cv_data.job_titles = json.dumps(job_titles)
        cv_data.updated_at = datetime.utcnow()
        
        # Update user profile with extracted information
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
        
        # Update profile only if fields are empty
        if not profile.phone and phone:
            profile.phone = phone
        if not profile.skills and skills:
            profile.skills = ', '.join(skills)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV uploaded and parsed successfully',
            'parsed_data': {
                'email': email,
                'phone': phone,
                'skills': skills,
                'keywords': all_keywords,
                'experience_years': experience_years,
                'education_level': education_level,
                'job_titles': job_titles,
                'text_length': len(extracted_text)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cv_parser_bp.route('/cv/data', methods=['GET'])
def get_cv_data():
    """Get parsed CV data for the current user"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        if not cv_data:
            return jsonify({'message': 'No CV data found'}), 404
        
        # Parse JSON fields
        keywords = []
        skills = []
        job_titles = []
        
        try:
            keywords = json.loads(cv_data.keywords) if cv_data.keywords else []
        except:
            keywords = []
        
        try:
            skills = json.loads(cv_data.skills) if cv_data.skills else []
        except:
            skills = []
        
        try:
            job_titles = json.loads(cv_data.job_titles) if cv_data.job_titles else []
        except:
            job_titles = []
        
        return jsonify({
            'cv_data': {
                'id': cv_data.id,
                'file_path': cv_data.file_path,
                'keywords': keywords,
                'skills': skills,
                'experience_years': cv_data.experience_years,
                'education_level': cv_data.education_level,
                'job_titles': job_titles,
                'text_length': len(cv_data.extracted_text) if cv_data.extracted_text else 0,
                'created_at': cv_data.created_at.isoformat() if cv_data.created_at else None,
                'updated_at': cv_data.updated_at.isoformat() if cv_data.updated_at else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cv_parser_bp.route('/cv/analyze', methods=['POST'])
def analyze_cv():
    """Analyze CV and provide improvement suggestions"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        target_job = data.get('target_job', '')
        language = data.get('language', 'en')
        
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        if not cv_data or not cv_data.extracted_text:
            return jsonify({'error': 'No CV data found. Please upload a CV first.'}), 404
        
        # Analyze CV using AI
        if language == 'ar':
            prompt = f"""حلل السيرة الذاتية التالية وقدم اقتراحات للتحسين:

السيرة الذاتية:
{cv_data.extracted_text[:3000]}

الوظيفة المستهدفة: {target_job}

يرجى تقديم تحليل شامل يتضمن:
1. نقاط القوة
2. نقاط الضعف
3. اقتراحات محددة للتحسين
4. كلمات مفتاحية مفقودة
5. تقييم عام من 10"""
        else:
            prompt = f"""Analyze the following CV and provide improvement suggestions:

CV Content:
{cv_data.extracted_text[:3000]}

Target Job: {target_job}

Please provide a comprehensive analysis including:
1. Strengths
2. Weaknesses
3. Specific improvement suggestions
4. Missing keywords
5. Overall rating out of 10"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert CV reviewer and career advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            
        except Exception as e:
            if language == 'ar':
                analysis = "عذراً، حدث خطأ في تحليل السيرة الذاتية. يرجى المحاولة مرة أخرى."
            else:
                analysis = "Sorry, there was an error analyzing the CV. Please try again."
        
        # Get basic statistics
        skills = []
        keywords = []
        
        try:
            skills = json.loads(cv_data.skills) if cv_data.skills else []
            keywords = json.loads(cv_data.keywords) if cv_data.keywords else []
        except:
            pass
        
        return jsonify({
            'analysis': analysis,
            'statistics': {
                'total_skills': len(skills),
                'total_keywords': len(keywords),
                'experience_years': cv_data.experience_years,
                'education_level': cv_data.education_level,
                'text_length': len(cv_data.extracted_text)
            },
            'target_job': target_job
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cv_parser_bp.route('/cv/keywords/suggest', methods=['POST'])
def suggest_keywords():
    """Suggest keywords to add to CV based on job requirements"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        job_description = data.get('job_description', '')
        language = data.get('language', 'en')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        cv_data = CVData.query.filter_by(user_id=user.id).first()
        
        if not cv_data:
            return jsonify({'error': 'No CV data found. Please upload a CV first.'}), 404
        
        # Get current CV keywords
        current_keywords = []
        try:
            current_keywords = json.loads(cv_data.keywords) if cv_data.keywords else []
        except:
            current_keywords = []
        
        # Extract keywords from job description
        job_keywords = extract_skills(job_description)
        
        # Find missing keywords
        missing_keywords = list(set(job_keywords) - set(current_keywords))
        
        # Use AI to suggest additional keywords
        if language == 'ar':
            prompt = f"""بناءً على وصف الوظيفة التالي:

{job_description[:2000]}

والكلمات المفتاحية الحالية في السيرة الذاتية:
{', '.join(current_keywords)}

اقترح كلمات مفتاحية إضافية يجب إضافتها للسيرة الذاتية لتحسين فرص القبول."""
        else:
            prompt = f"""Based on the following job description:

{job_description[:2000]}

And current CV keywords:
{', '.join(current_keywords)}

Suggest additional keywords that should be added to the CV to improve chances of acceptance."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in CV optimization and keyword matching."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.5
            )
            
            ai_suggestions = response.choices[0].message.content
            
        except Exception as e:
            ai_suggestions = "Error generating AI suggestions"
        
        return jsonify({
            'current_keywords': current_keywords,
            'job_keywords': job_keywords,
            'missing_keywords': missing_keywords,
            'ai_suggestions': ai_suggestions,
            'match_percentage': round(len(set(current_keywords).intersection(set(job_keywords))) / max(len(job_keywords), 1) * 100, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

