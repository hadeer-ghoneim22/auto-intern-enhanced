from flask import Blueprint, request, jsonify, current_app
import openai
import json
import uuid
from datetime import datetime
from src.models.user_enhanced import db, User, ChatSession, ChatMessage, Internship, Application
from src.routes.auth_enhanced_github import verify_token

ai_chatbot_bp = Blueprint('ai_chatbot', __name__)

# Initialize OpenAI client
openai.api_key = current_app.config.get('OPENAI_API_KEY') if current_app else None

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

def get_system_prompt(language='en'):
    """Get system prompt for the AI assistant"""
    if language == 'ar':
        return """أنت مساعد ذكي متخصص في مساعدة الطلاب والخريجين في العثور على فرص التدريب والوظائف. 
        يمكنك مساعدة المستخدمين في:
        1. البحث عن فرص التدريب المناسبة
        2. كتابة وتحسين رسائل التغطية
        3. تحليل السيرة الذاتية وتقديم النصائح
        4. التقديم التلقائي على الوظائف
        5. تتبع حالة الطلبات
        
        كن مفيداً ومهنياً في ردودك."""
    else:
        return """You are an AI assistant specialized in helping students and graduates find internship and job opportunities.
        You can help users with:
        1. Finding suitable internship opportunities
        2. Writing and improving cover letters
        3. Analyzing resumes and providing advice
        4. Automatically applying to jobs
        5. Tracking application status
        
        Be helpful and professional in your responses."""

@ai_chatbot_bp.route('/chat/start', methods=['POST'])
def start_chat_session():
    """Start a new chat session"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Create new chat session
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            user_id=user.id,
            session_id=session_id
        )
        
        db.session.add(chat_session)
        db.session.commit()
        
        return jsonify({
            'session_id': session_id,
            'message': 'Chat session started successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/chat/<session_id>/message', methods=['POST'])
def send_message(session_id):
    """Send a message to the AI chatbot"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        message = data.get('message', '').strip()
        language = data.get('language', 'en')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Find chat session
        chat_session = ChatSession.query.filter_by(
            session_id=session_id,
            user_id=user.id
        ).first()
        
        if not chat_session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        # Save user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            message_type='user',
            content=message
        )
        db.session.add(user_message)
        
        # Get chat history for context
        previous_messages = ChatMessage.query.filter_by(
            session_id=chat_session.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        # Build conversation context
        messages = [
            {"role": "system", "content": get_system_prompt(language)}
        ]
        
        # Add previous messages in reverse order (oldest first)
        for msg in reversed(previous_messages):
            role = "user" if msg.message_type == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get AI response
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as openai_error:
            # Fallback response if OpenAI fails
            if language == 'ar':
                ai_response = "عذراً، حدث خطأ في الاتصال بخدمة الذكاء الاصطناعي. يرجى المحاولة مرة أخرى."
            else:
                ai_response = "Sorry, there was an error connecting to the AI service. Please try again."
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=chat_session.id,
            message_type='assistant',
            content=ai_response
        )
        db.session.add(ai_message)
        
        # Update session timestamp
        chat_session.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/chat/<session_id>/history', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Find chat session
        chat_session = ChatSession.query.filter_by(
            session_id=session_id,
            user_id=user.id
        ).first()
        
        if not chat_session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        # Get messages
        messages = ChatMessage.query.filter_by(
            session_id=chat_session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'session_id': session_id,
            'messages': [msg.to_dict() for msg in messages]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/chat/sessions', methods=['GET'])
def get_user_chat_sessions():
    """Get all chat sessions for the current user"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        sessions = ChatSession.query.filter_by(
            user_id=user.id
        ).order_by(ChatSession.updated_at.desc()).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/ai/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    """Generate a cover letter using AI"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        job_title = data.get('job_title', '')
        company_name = data.get('company_name', '')
        job_description = data.get('job_description', '')
        user_skills = data.get('user_skills', '')
        user_experience = data.get('user_experience', '')
        language = data.get('language', 'en')
        
        if not job_title or not company_name:
            return jsonify({'error': 'Job title and company name are required'}), 400
        
        # Build prompt for cover letter generation
        if language == 'ar':
            prompt = f"""اكتب رسالة تغطية مهنية باللغة العربية للوظيفة التالية:

المسمى الوظيفي: {job_title}
اسم الشركة: {company_name}
وصف الوظيفة: {job_description}

معلومات المتقدم:
المهارات: {user_skills}
الخبرة: {user_experience}

يرجى كتابة رسالة تغطية مهنية ومقنعة تبرز مؤهلات المتقدم وتناسبها مع متطلبات الوظيفة."""
        else:
            prompt = f"""Write a professional cover letter for the following job:

Job Title: {job_title}
Company Name: {company_name}
Job Description: {job_description}

Applicant Information:
Skills: {user_skills}
Experience: {user_experience}

Please write a professional and compelling cover letter that highlights the applicant's qualifications and their fit for the position."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor specialized in writing cover letters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            cover_letter = response.choices[0].message.content
            
        except Exception as openai_error:
            if language == 'ar':
                cover_letter = "عذراً، حدث خطأ في توليد رسالة التغطية. يرجى المحاولة مرة أخرى."
            else:
                cover_letter = "Sorry, there was an error generating the cover letter. Please try again."
        
        return jsonify({
            'cover_letter': cover_letter,
            'job_title': job_title,
            'company_name': company_name
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/ai/job-recommendations', methods=['POST'])
def get_job_recommendations():
    """Get AI-powered job recommendations based on user profile"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        user_skills = data.get('user_skills', '')
        user_experience = data.get('user_experience', '')
        preferred_location = data.get('preferred_location', '')
        language = data.get('language', 'en')
        
        # Get available internships from database
        internships = Internship.query.limit(20).all()
        
        if not internships:
            if language == 'ar':
                return jsonify({'message': 'لا توجد فرص تدريب متاحة حالياً'}), 200
            else:
                return jsonify({'message': 'No internships available at the moment'}), 200
        
        # Build prompt for job matching
        internship_list = "\n".join([
            f"- {internship.title} at {internship.company} (Location: {internship.location or 'Not specified'})"
            for internship in internships
        ])
        
        if language == 'ar':
            prompt = f"""بناءً على المعلومات التالية للمستخدم:
المهارات: {user_skills}
الخبرة: {user_experience}
الموقع المفضل: {preferred_location}

من فضلك اختر أفضل 5 فرص تدريب مناسبة من القائمة التالية وقدم تفسيراً لكل اختيار:

{internship_list}

يرجى ترتيب الاختيارات حسب مدى الملاءمة وتقديم سبب لكل اختيار."""
        else:
            prompt = f"""Based on the following user information:
Skills: {user_skills}
Experience: {user_experience}
Preferred Location: {preferred_location}

Please select the top 5 most suitable internship opportunities from the following list and provide an explanation for each choice:

{internship_list}

Please rank the choices by suitability and provide a reason for each selection."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a career advisor specialized in matching candidates with suitable job opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            recommendations = response.choices[0].message.content
            
        except Exception as openai_error:
            if language == 'ar':
                recommendations = "عذراً، حدث خطأ في توليد التوصيات. يرجى المحاولة مرة أخرى."
            else:
                recommendations = "Sorry, there was an error generating recommendations. Please try again."
        
        return jsonify({
            'recommendations': recommendations,
            'total_internships': len(internships)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_chatbot_bp.route('/ai/improve-resume', methods=['POST'])
def improve_resume():
    """Get AI suggestions for resume improvement"""
    try:
        user = get_user_from_token(request)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        target_job = data.get('target_job', '')
        language = data.get('language', 'en')
        
        if not resume_text:
            return jsonify({'error': 'Resume text is required'}), 400
        
        if language == 'ar':
            prompt = f"""يرجى تحليل السيرة الذاتية التالية وتقديم اقتراحات للتحسين:

السيرة الذاتية:
{resume_text}

الوظيفة المستهدفة: {target_job}

يرجى تقديم:
1. نقاط القوة في السيرة الذاتية
2. المجالات التي تحتاج إلى تحسين
3. اقتراحات محددة للتحسين
4. كلمات مفتاحية مهمة يجب إضافتها"""
        else:
            prompt = f"""Please analyze the following resume and provide improvement suggestions:

Resume:
{resume_text}

Target Job: {target_job}

Please provide:
1. Strengths in the resume
2. Areas that need improvement
3. Specific suggestions for improvement
4. Important keywords to add"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume reviewer and career advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            suggestions = response.choices[0].message.content
            
        except Exception as openai_error:
            if language == 'ar':
                suggestions = "عذراً، حدث خطأ في تحليل السيرة الذاتية. يرجى المحاولة مرة أخرى."
            else:
                suggestions = "Sorry, there was an error analyzing the resume. Please try again."
        
        return jsonify({
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

