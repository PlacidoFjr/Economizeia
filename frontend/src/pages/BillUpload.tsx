import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import api from '../services/api'
import { Upload, FileText, X } from 'lucide-react'

export default function BillUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const navigate = useNavigate()

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post('/bills/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: (data) => {
      navigate(`/app/bills/${data.bill_id}`)
    },
    onError: (error: any) => {
      console.error('Erro no upload:', error)
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleFileButtonClick = () => {
    const fileInput = document.getElementById('file-upload') as HTMLInputElement
    if (fileInput) {
      fileInput.click()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4 sm:space-y-6 p-4 sm:p-6 min-h-screen bg-gray-50">
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Enviar Boleto</h1>
        <p className="text-sm text-gray-600">Faça upload do seu boleto ou fatura para processamento automático</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-6 sm:p-12 text-center transition-all ${
            dragActive
              ? 'border-gray-400 bg-gray-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          {file ? (
            <div className="space-y-3 sm:space-y-4">
              <div className="bg-gray-100 w-16 h-16 sm:w-20 sm:h-20 rounded-full flex items-center justify-center mx-auto">
                <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-gray-600" />
              </div>
              <div>
                <p className="text-lg font-semibold text-gray-900 mb-1">{file.name}</p>
                <p className="text-sm text-gray-600">
                  Tamanho: {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 hover:underline"
              >
                Remover arquivo
              </button>
            </div>
          ) : (
            <div className="space-y-4 sm:space-y-5">
              <div className="bg-gray-100 w-16 h-16 sm:w-20 sm:h-20 rounded-full flex items-center justify-center mx-auto">
                <Upload className="w-8 h-8 sm:w-10 sm:h-10 text-gray-600" />
              </div>
              <div>
                <button
                  type="button"
                  onClick={handleFileButtonClick}
                  className="cursor-pointer inline-flex items-center px-4 sm:px-4 py-2.5 sm:py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Selecionar Arquivo
                </button>
                <input
                  id="file-upload"
                  type="file"
                  className="hidden"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleFileChange}
                />
                <p className="text-sm text-gray-600 mt-3">
                  ou arraste e solte o arquivo aqui
                </p>
              </div>
              <div className="bg-gray-50 rounded-md p-3 border border-gray-200">
                <p className="text-xs font-medium text-gray-700 uppercase tracking-wide mb-1">
                  Formatos Suportados
                </p>
                <p className="text-xs text-gray-600">
                  PDF, PNG, JPG, JPEG (tamanho máximo: 10MB)
                </p>
              </div>
            </div>
          )}
        </div>

        {file && (
          <button
            type="submit"
            disabled={uploadMutation.isPending}
            className="w-full flex justify-center items-center py-3.5 sm:py-3 px-4 border border-transparent text-base sm:text-sm font-semibold rounded-md text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploadMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Enviando...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Enviar Boleto
              </>
            )}
          </button>
        )}

        {uploadMutation.isError && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-md p-3">
            <div className="flex items-center">
              <div className="bg-red-100 p-1.5 rounded mr-2">
                <X className="w-4 h-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Erro ao fazer upload</p>
                <p className="text-xs text-red-600 mt-0.5">
                  {uploadMutation.error?.response?.data?.detail || 
                   uploadMutation.error?.message || 
                   'Tente novamente ou verifique o arquivo'}
                </p>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}
