import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import ToastContainer from './components/ToastContainer'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import VerifyEmail from './pages/VerifyEmail'
import TermosUso from './pages/TermosUso'
import Privacidade from './pages/Privacidade'
import Dashboard from './pages/Dashboard'
import Bills from './pages/Bills'
import Finances from './pages/Finances'
import BillUpload from './pages/BillUpload'
import BillDetail from './pages/BillDetail'
import Payments from './pages/Payments'
import Installments from './pages/Installments'
import AddExpense from './pages/AddExpense'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastContainer>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/termos" element={<TermosUso />} />
            <Route path="/privacidade" element={<Privacidade />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="bills" element={<Bills />} />
              <Route path="bills/upload" element={<BillUpload />} />
              <Route path="bills/add" element={<AddExpense />} />
              <Route path="bills/:id" element={<BillDetail />} />
              <Route path="finances" element={<Finances />} />
              <Route path="payments" element={<Payments />} />
              <Route path="installments" element={<Installments />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      </ToastContainer>
    </QueryClientProvider>
  )
}

export default App

