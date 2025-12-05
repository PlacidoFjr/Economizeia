import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
}

export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav className="flex items-center space-x-1 sm:space-x-2 text-sm mb-4 sm:mb-6" aria-label="Breadcrumb">
      <Link
        to="/app/dashboard"
        className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
        aria-label="Painel"
      >
        <Home className="w-4 h-4" aria-hidden="true" />
      </Link>
      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-1 sm:space-x-2">
          <ChevronRight className="w-4 h-4 text-gray-400" aria-hidden="true" />
          {item.to ? (
            <Link
              to={item.to}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-900 font-medium">{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  )
}

