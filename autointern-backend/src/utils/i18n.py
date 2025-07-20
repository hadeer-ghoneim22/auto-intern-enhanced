"""
Internationalization (i18n) utility for Auto Intern project
Supports Arabic and English languages
"""

import json
import os
from flask import request, session

class I18n:
    def __init__(self, app=None):
        self.app = app
        self.translations = {}
        self.default_language = 'en'
        self.supported_languages = ['en', 'ar']
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the i18n extension with Flask app"""
        self.app = app
        self.load_translations()
        
        # Add template global functions
        app.jinja_env.globals['_'] = self.translate
        app.jinja_env.globals['get_language'] = self.get_language
        app.jinja_env.globals['get_rtl'] = self.is_rtl
    
    def load_translations(self):
        """Load translation files"""
        translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
        
        for lang in self.supported_languages:
            translation_file = os.path.join(translations_dir, f'{lang}.json')
            if os.path.exists(translation_file):
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
            else:
                self.translations[lang] = {}
    
    def get_language(self):
        """Get current language from session, request, or default"""
        # Check session first
        if 'language' in session:
            return session['language']
        
        # Check request headers
        if request and hasattr(request, 'headers'):
            accept_language = request.headers.get('Accept-Language', '')
            if 'ar' in accept_language:
                return 'ar'
        
        # Check request args
        if request and hasattr(request, 'args'):
            lang = request.args.get('lang')
            if lang in self.supported_languages:
                return lang
        
        return self.default_language
    
    def set_language(self, language):
        """Set language in session"""
        if language in self.supported_languages:
            session['language'] = language
            return True
        return False
    
    def translate(self, key, language=None, **kwargs):
        """Translate a key to the specified language"""
        if language is None:
            language = self.get_language()
        
        if language not in self.translations:
            language = self.default_language
        
        # Get translation
        translation = self.translations[language].get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return translation
    
    def is_rtl(self, language=None):
        """Check if language is right-to-left"""
        if language is None:
            language = self.get_language()
        return language == 'ar'
    
    def get_direction(self, language=None):
        """Get text direction for language"""
        return 'rtl' if self.is_rtl(language) else 'ltr'

# Global instance
i18n = I18n()

# Translation data
TRANSLATIONS = {
    'en': {
        # General
        'app_name': 'Auto Intern',
        'welcome': 'Welcome',
        'login': 'Login',
        'logout': 'Logout',
        'signup': 'Sign Up',
        'email': 'Email',
        'password': 'Password',
        'name': 'Name',
        'phone': 'Phone',
        'submit': 'Submit',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'search': 'Search',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'language': 'Language',
        'english': 'English',
        'arabic': 'Arabic',
        
        # Navigation
        'dashboard': 'Dashboard',
        'jobs': 'Jobs',
        'applications': 'Applications',
        'profile': 'Profile',
        'cv': 'CV',
        'chat': 'Chat',
        'settings': 'Settings',
        
        # Authentication
        'login_with_github': 'Login with GitHub',
        'login_with_google': 'Login with Google',
        'create_account': 'Create Account',
        'forgot_password': 'Forgot Password?',
        'remember_me': 'Remember Me',
        'login_success': 'Login successful',
        'logout_success': 'Logout successful',
        'signup_success': 'Account created successfully',
        'invalid_credentials': 'Invalid email or password',
        
        # Jobs
        'job_search': 'Job Search',
        'job_title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'description': 'Description',
        'requirements': 'Requirements',
        'apply_now': 'Apply Now',
        'auto_apply': 'Auto Apply',
        'job_recommendations': 'Job Recommendations',
        'search_jobs': 'Search Jobs',
        'no_jobs_found': 'No jobs found',
        'job_applied': 'Application submitted successfully',
        
        # Applications
        'my_applications': 'My Applications',
        'application_status': 'Application Status',
        'applied_date': 'Applied Date',
        'status_submitted': 'Submitted',
        'status_under_review': 'Under Review',
        'status_interview': 'Interview Scheduled',
        'status_accepted': 'Accepted',
        'status_rejected': 'Rejected',
        'application_tracker': 'Application Tracker',
        'total_applications': 'Total Applications',
        'success_rate': 'Success Rate',
        
        # CV
        'upload_cv': 'Upload CV',
        'cv_analysis': 'CV Analysis',
        'cv_uploaded': 'CV uploaded successfully',
        'cv_parsed': 'CV parsed successfully',
        'skills_extracted': 'Skills extracted',
        'keywords_found': 'Keywords found',
        'experience_years': 'Years of Experience',
        'education_level': 'Education Level',
        'improve_cv': 'Improve CV',
        'cv_suggestions': 'CV Suggestions',
        
        # Chat
        'ai_assistant': 'AI Assistant',
        'start_chat': 'Start Chat',
        'type_message': 'Type your message...',
        'send_message': 'Send',
        'chat_history': 'Chat History',
        'new_chat': 'New Chat',
        
        # Autofill
        'autofill': 'Autofill',
        'detect_fields': 'Detect Fields',
        'fill_form': 'Fill Form',
        'autofill_success': 'Form filled successfully',
        'autofill_profile': 'Autofill Profile',
        'update_profile': 'Update Profile',
        
        # Profile
        'personal_info': 'Personal Information',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'linkedin_url': 'LinkedIn URL',
        'github_url': 'GitHub URL',
        'portfolio_url': 'Portfolio URL',
        'skills': 'Skills',
        'experience': 'Experience',
        'education': 'Education',
        'bio': 'Bio',
        'profile_updated': 'Profile updated successfully',
        
        # Cover Letter
        'cover_letter': 'Cover Letter',
        'generate_cover_letter': 'Generate Cover Letter',
        'cover_letter_generated': 'Cover letter generated successfully',
        'improve_cover_letter': 'Improve Cover Letter',
        
        # Messages
        'required_field': 'This field is required',
        'invalid_email': 'Please enter a valid email address',
        'password_too_short': 'Password must be at least 6 characters',
        'file_too_large': 'File size too large',
        'invalid_file_type': 'Invalid file type',
        'network_error': 'Network error. Please try again.',
        'server_error': 'Server error. Please try again later.',
    },
    
    'ar': {
        # General
        'app_name': 'أوتو إنترن',
        'welcome': 'مرحباً',
        'login': 'تسجيل الدخول',
        'logout': 'تسجيل الخروج',
        'signup': 'إنشاء حساب',
        'email': 'البريد الإلكتروني',
        'password': 'كلمة المرور',
        'name': 'الاسم',
        'phone': 'الهاتف',
        'submit': 'إرسال',
        'cancel': 'إلغاء',
        'save': 'حفظ',
        'delete': 'حذف',
        'edit': 'تعديل',
        'search': 'بحث',
        'loading': 'جاري التحميل...',
        'error': 'خطأ',
        'success': 'نجح',
        'language': 'اللغة',
        'english': 'الإنجليزية',
        'arabic': 'العربية',
        
        # Navigation
        'dashboard': 'لوحة التحكم',
        'jobs': 'الوظائف',
        'applications': 'الطلبات',
        'profile': 'الملف الشخصي',
        'cv': 'السيرة الذاتية',
        'chat': 'المحادثة',
        'settings': 'الإعدادات',
        
        # Authentication
        'login_with_github': 'تسجيل الدخول بـ GitHub',
        'login_with_google': 'تسجيل الدخول بـ Google',
        'create_account': 'إنشاء حساب',
        'forgot_password': 'نسيت كلمة المرور؟',
        'remember_me': 'تذكرني',
        'login_success': 'تم تسجيل الدخول بنجاح',
        'logout_success': 'تم تسجيل الخروج بنجاح',
        'signup_success': 'تم إنشاء الحساب بنجاح',
        'invalid_credentials': 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
        
        # Jobs
        'job_search': 'البحث عن وظائف',
        'job_title': 'المسمى الوظيفي',
        'company': 'الشركة',
        'location': 'الموقع',
        'description': 'الوصف',
        'requirements': 'المتطلبات',
        'apply_now': 'تقدم الآن',
        'auto_apply': 'تقديم تلقائي',
        'job_recommendations': 'توصيات الوظائف',
        'search_jobs': 'البحث عن وظائف',
        'no_jobs_found': 'لم يتم العثور على وظائف',
        'job_applied': 'تم تقديم الطلب بنجاح',
        
        # Applications
        'my_applications': 'طلباتي',
        'application_status': 'حالة الطلب',
        'applied_date': 'تاريخ التقديم',
        'status_submitted': 'مُرسل',
        'status_under_review': 'قيد المراجعة',
        'status_interview': 'مقابلة مجدولة',
        'status_accepted': 'مقبول',
        'status_rejected': 'مرفوض',
        'application_tracker': 'متتبع الطلبات',
        'total_applications': 'إجمالي الطلبات',
        'success_rate': 'معدل النجاح',
        
        # CV
        'upload_cv': 'رفع السيرة الذاتية',
        'cv_analysis': 'تحليل السيرة الذاتية',
        'cv_uploaded': 'تم رفع السيرة الذاتية بنجاح',
        'cv_parsed': 'تم تحليل السيرة الذاتية بنجاح',
        'skills_extracted': 'المهارات المستخرجة',
        'keywords_found': 'الكلمات المفتاحية الموجودة',
        'experience_years': 'سنوات الخبرة',
        'education_level': 'المستوى التعليمي',
        'improve_cv': 'تحسين السيرة الذاتية',
        'cv_suggestions': 'اقتراحات السيرة الذاتية',
        
        # Chat
        'ai_assistant': 'المساعد الذكي',
        'start_chat': 'بدء محادثة',
        'type_message': 'اكتب رسالتك...',
        'send_message': 'إرسال',
        'chat_history': 'تاريخ المحادثات',
        'new_chat': 'محادثة جديدة',
        
        # Autofill
        'autofill': 'التعبئة التلقائية',
        'detect_fields': 'اكتشاف الحقول',
        'fill_form': 'تعبئة النموذج',
        'autofill_success': 'تم تعبئة النموذج بنجاح',
        'autofill_profile': 'ملف التعبئة التلقائية',
        'update_profile': 'تحديث الملف الشخصي',
        
        # Profile
        'personal_info': 'المعلومات الشخصية',
        'first_name': 'الاسم الأول',
        'last_name': 'اسم العائلة',
        'linkedin_url': 'رابط LinkedIn',
        'github_url': 'رابط GitHub',
        'portfolio_url': 'رابط المعرض',
        'skills': 'المهارات',
        'experience': 'الخبرة',
        'education': 'التعليم',
        'bio': 'نبذة شخصية',
        'profile_updated': 'تم تحديث الملف الشخصي بنجاح',
        
        # Cover Letter
        'cover_letter': 'رسالة التغطية',
        'generate_cover_letter': 'توليد رسالة التغطية',
        'cover_letter_generated': 'تم توليد رسالة التغطية بنجاح',
        'improve_cover_letter': 'تحسين رسالة التغطية',
        
        # Messages
        'required_field': 'هذا الحقل مطلوب',
        'invalid_email': 'يرجى إدخال عنوان بريد إلكتروني صحيح',
        'password_too_short': 'يجب أن تكون كلمة المرور 6 أحرف على الأقل',
        'file_too_large': 'حجم الملف كبير جداً',
        'invalid_file_type': 'نوع الملف غير صحيح',
        'network_error': 'خطأ في الشبكة. يرجى المحاولة مرة أخرى.',
        'server_error': 'خطأ في الخادم. يرجى المحاولة لاحقاً.',
    }
}

def create_translation_files():
    """Create translation files in the translations directory"""
    translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
    os.makedirs(translations_dir, exist_ok=True)
    
    for lang, translations in TRANSLATIONS.items():
        file_path = os.path.join(translations_dir, f'{lang}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

# Create translation files when module is imported
create_translation_files()

