import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import ToastContainer from './components/ToastContainer'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'

// Lazy load das páginas públicas (menos críticas)
const Home = lazy(() => import('./pages/Home'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'))
const TermosUso = lazy(() => import('./pages/TermosUso'))
const Privacidade = lazy(() => import('./pages/Privacidade'))

// Lazy load das páginas protegidas (mais pesadas)
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Bills = lazy(() => import('./pages/Bills'))
const Finances = lazy(() => import('./pages/Finances'))
const BillUpload = lazy(() => import('./pages/BillUpload'))
const BillDetail = lazy(() => import('./pages/BillDetail'))
const Payments = lazy(() => import('./pages/Payments'))
const Installments = lazy(() => import('./pages/Installments'))
const AddExpense = lazy(() => import('./pages/AddExpense'))
const SavingsGoals = lazy(() => import('./pages/SavingsGoals'))
const Investments = lazy(() => import('./pages/Investments'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 10 * 60 * 1000, // 10 minutos
      refetchOnWindowFocus: false,
    },
  },
})

// Componente de Suspense reutilizável
const PageSuspense = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingSpinner message="Carregando página..." />}>
    {children}
  </Suspense>
)

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastContainer>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            <Route path="/" element={<PageSuspense><Home /></PageSuspense>} />
            <Route path="/login" element={<PageSuspense><Login /></PageSuspense>} />
            <Route path="/register" element={<PageSuspense><Register /></PageSuspense>} />
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
              <Route path="bills" element={<PageSuspense><Bills /></PageSuspense>} />
              <Route path="bills/upload" element={<PageSuspense><BillUpload /></PageSuspense>} />
              <Route path="bills/add" element={<PageSuspense><AddExpense /></PageSuspense>} />
              <Route path="bills/:id" element={<PageSuspense><BillDetail /></PageSuspense>} />
              <Route path="finances" element={<PageSuspense><Finances /></PageSuspense>} />
              <Route path="payments" element={<PageSuspense><Payments /></PageSuspense>} />
              <Route path="installments" element={<PageSuspense><Installments /></PageSuspense>} />
              <Route path="savings-goals" element={<PageSuspense><SavingsGoals /></PageSuspense>} />
              <Route path="investments" element={<PageSuspense><Investments /></PageSuspense>} />
            </Route>
            {/* Redirect antigo /dashboard para /app/dashboard */}
            <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      </ToastContainer>
    </QueryClientProvider>
  )
}

export default App

