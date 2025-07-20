# AutoIntern.AI 🚀

An AI-powered internship assistant that helps students discover opportunities, write applications, and track their progress.

## 🌟 Features

- **🔍 Opportunity Discovery**: LinkedIn integration to find relevant internships
- **✍️ AI-Powered Writing**: Generate personalized cover letters and applications
- **📊 Application Tracking**: Monitor application status and progress
- **🤖 AI Assistant**: Get career guidance and interview preparation help
- **🔐 Secure Authentication**: Google Sign-In and email authentication
- **📱 Mobile-First Design**: Responsive design optimized for mobile devices

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern UI component library
- **Lucide React** - Beautiful icons

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Development database
- **Supabase** - Production database (optional)
- **JWT** - Authentication tokens

### AI & Integrations
- **OpenAI API** - AI-powered content generation
- **Google Sign-In** - OAuth authentication
- **LinkedIn API** - Job opportunity discovery

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- Git

### 1. Clone the Repository
\`\`\`bash
git clone <repository-url>
cd autointern-ai
\`\`\`

### 2. Install Frontend Dependencies
\`\`\`bash
npm install
# or
yarn install
\`\`\`

### 3. Install Backend Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Set Up Environment Variables
Copy the `.env` file and configure your environment variables:
\`\`\`bash
cp .env.example .env
\`\`\`

Required environment variables:
\`\`\`env
# Supabase (optional)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# OpenAI (for AI features)
OPENAI_API_KEY=your_openai_api_key
\`\`\`

### 5. Set Up the Database
\`\`\`bash
# Create database and add sample data
npm run setup-backend

# Or run Python scripts directly
python scripts/setup_database.py
python scripts/seed_data.py
\`\`\`

### 6. Start Development Servers

**Frontend (Next.js):**
\`\`\`bash
npm run dev
\`\`\`

**Backend (Flask):**
\`\`\`bash
cd backend
python app.py
\`\`\`

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## 📁 Project Structure

\`\`\`
autointern-ai/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── dashboard.tsx     # Main dashboard
│   ├── login-screen.tsx  # Authentication
│   └── ...               # Feature components
├── lib/                  # Utility libraries
│   ├── api.ts           # API client
│   └── utils.ts         # Helper functions
├── scripts/             # Database and setup scripts
│   ├── create_db.py     # Database creation
│   ├── setup_database.py # Enhanced setup
│   └── seed_data.py     # Sample data
├── backend/             # Flask backend (if separate)
├── requirements.txt     # Python dependencies
├── package.json        # Node.js dependencies
└── README.md           # This file
\`\`\`

## 🗄️ Database Schema

### Users Table
- `id` - Primary key
- `email` - User email (unique)
- `password_hash` - Hashed password
- `google_id` - Google OAuth ID
- `name` - User display name
- `created_at`, `updated_at` - Timestamps

### Internships Table
- `id` - Primary key
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `description` - Job description
- `url` - Application URL
- `requirements` - Job requirements
- `salary_range` - Compensation range
- `duration` - Internship duration
- `application_deadline` - Application deadline

### Applications Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `internship_id` - Foreign key to internships
- `status` - Application status
- `applied_date` - Application date
- `cover_letter` - Generated cover letter
- `notes` - User notes

## 🔧 Available Scripts

### Frontend
\`\`\`bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
\`\`\`

### Backend & Database
\`\`\`bash
npm run setup-db     # Create database with original script
npm run seed-db      # Add additional sample data
npm run setup-backend # Complete backend setup
\`\`\`

### Python Scripts
\`\`\`bash
python scripts/setup_database.py  # Enhanced database setup
python scripts/seed_data.py       # Add comprehensive test data
python scripts/create_db.py       # Original database creation
\`\`\`

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/google-login` - Google OAuth login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - User logout

### Internships
- `GET /api/internships` - List internships
- `POST /api/internships/apply` - Apply to internship

### Applications
- `GET /api/applications` - User's applications
- `PUT /api/applications/:id` - Update application status

## 🎨 UI Components

The application uses shadcn/ui components for a consistent, modern interface:

- **Forms**: Input, Label, Button, Select
- **Navigation**: Breadcrumb, Command, Navigation Menu
- **Feedback**: Alert, Toast, Progress
- **Data Display**: Card, Table, Badge, Avatar
- **Overlays**: Dialog, Popover, Tooltip
- **Layout**: Accordion, Tabs, Separator

## 🔐 Authentication Flow

1. **Google Sign-In**: OAuth 2.0 flow with Google
2. **Email/Password**: Traditional authentication
3. **JWT Tokens**: Secure session management
4. **Token Refresh**: Automatic token renewal
5. **Secure Storage**: Client-side token storage

## 🤖 AI Features

- **Cover Letter Generation**: Personalized based on job and user profile
- **Application Assistance**: AI-powered writing suggestions
- **Interview Preparation**: Practice questions and tips
- **Career Guidance**: Personalized advice and recommendations

## 📱 Mobile Optimization

- **Responsive Design**: Mobile-first approach
- **Touch-Friendly**: Optimized for touch interactions
- **Progressive Web App**: PWA capabilities
- **Offline Support**: Basic offline functionality

## 🚀 Deployment

### Frontend (Vercel)
\`\`\`bash
npm run build
# Deploy to Vercel
\`\`\`

### Backend (Railway/Heroku)
\`\`\`bash
# Set up production database
# Configure environment variables
# Deploy Flask application
\`\`\`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **shadcn/ui** for the beautiful component library
- **Vercel** for the excellent Next.js framework
- **Supabase** for the backend infrastructure
- **OpenAI** for AI capabilities
- **Lucide** for the icon library

## 📞 Support

For support, email support@autointern.ai or join our Discord community.

---

**Built with ❤️ for students seeking amazing internship opportunities**
