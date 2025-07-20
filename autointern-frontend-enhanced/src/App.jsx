import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  User, 
  Briefcase, 
  FileText, 
  MessageSquare, 
  Settings, 
  Search, 
  Upload, 
  Bot, 
  Globe, 
  Github, 
  Mail,
  Phone,
  MapPin,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Send,
  Download,
  Plus,
  Edit,
  Trash2,
  Languages
} from 'lucide-react'
import './App.css'

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api'

// Language Context
const LanguageContext = React.createContext()

// Translation hook
const useTranslation = () => {
  const context = React.useContext(LanguageContext)
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider')
  }
  return context
}

// Language Provider Component
const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState('en')
  const [translations, setTranslations] = useState({})
  const [isRTL, setIsRTL] = useState(false)

  useEffect(() => {
    loadTranslations(language)
  }, [language])

  const loadTranslations = async (lang) => {
    try {
      const response = await fetch(`${API_BASE_URL}/i18n/translations/${lang}`)
      const data = await response.json()
      setTranslations(data.translations || {})
      setIsRTL(data.is_rtl || false)
    } catch (error) {
      console.error('Failed to load translations:', error)
    }
  }

  const t = (key, params = {}) => {
    let translation = translations[key] || key
    Object.keys(params).forEach(param => {
      translation = translation.replace(`{${param}}`, params[param])
    })
    return translation
  }

  const changeLanguage = async (newLanguage) => {
    try {
      await fetch(`${API_BASE_URL}/i18n/language`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: newLanguage })
      })
      setLanguage(newLanguage)
    } catch (error) {
      console.error('Failed to change language:', error)
    }
  }

  return (
    <LanguageContext.Provider value={{ language, t, changeLanguage, isRTL }}>
      <div dir={isRTL ? 'rtl' : 'ltr'} className={isRTL ? 'rtl' : 'ltr'}>
        {children}
      </div>
    </LanguageContext.Provider>
  )
}

// Authentication Context
const AuthContext = React.createContext()

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        logout()
      }
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = (userData, userToken) => {
    setUser(userData)
    setToken(userToken)
    localStorage.setItem('token', userToken)
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

const useAuth = () => {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Header Component
const Header = () => {
  const { t, language, changeLanguage, isRTL } = useTranslation()
  const { user, logout } = useAuth()

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Briefcase className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">{t('app_name')}</span>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Language Switcher */}
            <Select value={language} onValueChange={changeLanguage}>
              <SelectTrigger className="w-32">
                <Languages className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">{t('english')}</SelectItem>
                <SelectItem value="ar">{t('arabic')}</SelectItem>
              </SelectContent>
            </Select>

            {user && (
              <>
                <span className="text-sm text-gray-700">{t('welcome')}, {user.name}</span>
                <Button variant="outline" onClick={logout}>
                  {t('logout')}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

// Login Component
const Login = () => {
  const { t } = useTranslation()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok) {
        login(data, data.token)
      } else {
        setError(data.error || t('invalid_credentials'))
      }
    } catch (error) {
      setError(t('network_error'))
    } finally {
      setLoading(false)
    }
  }

  const handleGitHubLogin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/github/login`)
      const data = await response.json()
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    } catch (error) {
      setError(t('network_error'))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center">
            <Briefcase className="h-12 w-12 text-blue-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {t('login')}
          </h2>
        </div>
        
        <Card>
          <CardContent className="p-6">
            {error && (
              <Alert className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Input
                  type="email"
                  placeholder={t('email')}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <Input
                  type="password"
                  placeholder={t('password')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? t('loading') : t('login')}
              </Button>
            </form>
            
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Or</span>
                </div>
              </div>
              
              <div className="mt-6 space-y-3">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleGitHubLogin}
                >
                  <Github className="h-4 w-4 mr-2" />
                  {t('login_with_github')}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Dashboard Component
const Dashboard = () => {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [stats, setStats] = useState({
    total_applications: 0,
    success_rate: 0,
    recent_applications: 0
  })

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/applications/tracker`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data.summary)
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard')}</h1>
        <p className="text-gray-600">{t('welcome')}, {user?.name}!</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('total_applications')}</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_applications}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('success_rate')}</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.success_rate}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('recent_applications')}</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.recent_applications}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{t('ai_assistant')}</CardTitle>
            <CardDescription>
              Get help with job search, cover letters, and more
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full">
              <MessageSquare className="h-4 w-4 mr-2" />
              {t('start_chat')}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('cv_analysis')}</CardTitle>
            <CardDescription>
              Upload and analyze your CV for better job matching
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              {t('upload_cv')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Main App Component
const MainApp = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Briefcase className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <Dashboard />
      </main>
    </div>
  )
}

// Root App Component
function App() {
  return (
    <Router>
      <LanguageProvider>
        <AuthProvider>
          <MainApp />
        </AuthProvider>
      </LanguageProvider>
    </Router>
  )
}

export default App

