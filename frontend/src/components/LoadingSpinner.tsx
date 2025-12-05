interface LoadingSpinnerProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export default function LoadingSpinner({ message = 'Carregando...', size = 'md' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] py-12">
      <div className={`animate-spin rounded-full border-b-2 border-gray-900 ${sizeClasses[size]} mb-4`}></div>
      <p className="text-sm text-gray-600">{message}</p>
    </div>
  )
}

