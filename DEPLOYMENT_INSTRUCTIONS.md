# Auto Intern Enhanced - Quick Deployment Guide

## Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API Key
- GitHub OAuth App (optional)

## Quick Start (Development)

### 1. Backend Setup
```bash
cd autointern-backend
pip install -r requirements_enhanced.txt

# Create .env file
echo "SECRET_KEY=your-secret-key" > .env
echo "OPENAI_API_KEY=your-openai-key" >> .env
echo "DATABASE_URL=sqlite:///autointern.db" >> .env

# Start backend
python main_enhanced.py
```

### 2. Frontend Setup
```bash
cd autointern-frontend-enhanced
npm install
npm run dev --host
```

### 3. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/api/info

## Production Deployment

### Using Docker Compose
```bash
# Create docker-compose.yml (see full documentation)
docker-compose up -d
```

### Manual Production Setup
```bash
# Backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main_enhanced:app

# Frontend
npm run build
serve -s dist -l 3000
```

## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Flask secret key

### Optional
- `GITHUB_CLIENT_ID`: GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth client secret
- `DATABASE_URL`: Database connection string

## Features Available

✅ **Implemented Features:**
- GitHub OAuth Authentication
- AI Chatbot (OpenAI GPT-3.5)
- Autofill System (Selenium-based)
- Job Search & Recommendations
- Application Tracker
- CV Parser with AI Analysis
- Multilingual Support (Arabic/English)
- Cover Letter Generation

🔧 **Configuration Required:**
- OpenAI API key for AI features
- GitHub OAuth for social login
- Selenium WebDriver for autofill

📝 **Next Steps:**
1. Configure OAuth applications
2. Set up production database
3. Configure file storage for CV uploads
4. Set up monitoring and logging
5. Implement SSL certificates

For detailed documentation, see `AUTO_INTERN_ENHANCED_DOCUMENTATION.md`

