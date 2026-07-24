import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import ToastContainer from './components/ToastContainer'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'

const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'))
const TermosUso = lazy(() => import('./pages/TermosUso'))
const Privacidade = lazy(() => import('./pages/Privacidade'))

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Finances = lazy(() => import('./pages/Finances'))
const Payments = lazy(() => import('./pages/Payments'))
const Installments = lazy(() => import('./pages/Installments'))
const AddExpense = lazy(() => import('./pages/AddExpense'))
const SavingsGoals = lazy(() => import('./pages/SavingsGoals'))
const Investments = lazy(() => import('./pages/Investments'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
})

const PageSuspense = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingSpinner message="Carregando página..." />}>{children}</Suspense>
)

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastContainer>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<PageSuspense><ForgotPassword /></PageSuspense>} />
                <Route path="/reset-password" element={<PageSuspense><ResetPassword /></PageSuspense>} />
                <Route path="/verify-email" element={<PageSuspense><VerifyEmail /></PageSuspense>} />
                <Route path="/termos" element={<PageSuspense><TermosUso /></PageSuspense>} />
                <Route path="/privacidade" element={<PageSuspense><Privacidade /></PageSuspense>} />
                <Route
                  path="/app"
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<Navigate to="/app/dashboard" replace />} />
                  <Route path="dashboard" element={<PageSuspense><Dashboard /></PageSuspense>} />
                  <Route path="bills" element={<Navigate to="/app/finances" replace />} />
                  <Route path="bills/upload" element={<Navigate to="/app/transactions/add" replace />} />
                  <Route path="bills/add" element={<Navigate to="/app/transactions/add" replace />} />
                  <Route path="bills/:id" element={<Navigate to="/app/finances" replace />} />
                  <Route path="transactions/add" element={<PageSuspense><AddExpense /></PageSuspense>} />
                  <Route path="finances" element={<PageSuspense><Finances /></PageSuspense>} />
                  <Route path="payments" element={<PageSuspense><Payments /></PageSuspense>} />
                  <Route path="installments" element={<PageSuspense><Installments /></PageSuspense>} />
                  <Route path="savings-goals" element={<PageSuspense><SavingsGoals /></PageSuspense>} />
                  <Route path="investments" element={<PageSuspense><Investments /></PageSuspense>} />
                </Route>
                <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </ToastContainer>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
