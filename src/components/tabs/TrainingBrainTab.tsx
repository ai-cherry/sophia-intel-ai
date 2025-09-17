import { useState, useRef } from 'react'

export default function TrainingBrainTab() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const knowledgeSources = [
    {
      name: 'Company Documents',
      type: 'PDF/DOCX',
      status: 'processed',
      size: '45.2 MB',
      lastUpdated: '2 hours ago',
      documents: 127
    },
    {
      name: 'Business Processes',
      type: 'Markdown',
      status: 'processing',
      size: '12.8 MB',
      lastUpdated: '30 minutes ago',
      documents: 34
    },
    {
      name: 'Customer Data',
      type: 'CSV/JSON',
      status: 'processed',
      size: '89.1 MB',
      lastUpdated: '1 day ago',
      documents: 256
    },
    {
      name: 'Code Repository',
      type: 'Source Code',
      status: 'indexed',
      size: '234.5 MB',
      lastUpdated: '6 hours ago',
      documents: 1842
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-100'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800/30 dark:text-yellow-100'
      case 'indexed':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800/30 dark:text-blue-100'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-800/30 dark:text-red-100'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-100'
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFiles(files)
      handleFileUpload(files)
    }
  }

  const handleFileUpload = (files: FileList) => {
    setIsProcessing(true)
    // Simulate upload progress
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      setUploadProgress(progress)
      if (progress >= 100) {
        clearInterval(interval)
        setIsProcessing(false)
        setUploadProgress(0)
        alert(`Successfully uploaded ${files.length} file(s)`)
        setSelectedFiles(null)
      }
    }, 200)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.add('border-accent', 'bg-accent/5')
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('border-accent', 'bg-accent/5')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.remove('border-accent', 'bg-accent/5')

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      setSelectedFiles(files)
      handleFileUpload(files)
    }
  }

  const handleSourceClick = (source: string) => {
    alert(`Coming Soon: Upload from ${source}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary mb-2">Training Sophia's Brain</h2>
        <p className="text-secondary">Knowledge ingestion and AI model training</p>
      </div>

      {/* Knowledge Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🧠</div>
            <div>
              <div className="text-2xl font-bold text-primary">2,259</div>
              <div className="text-sm text-secondary">Documents Processed</div>
            </div>
          </div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center">
            <div className="text-2xl mr-3">📚</div>
            <div>
              <div className="text-2xl font-bold text-accent">381.6 MB</div>
              <div className="text-sm text-secondary">Knowledge Base Size</div>
            </div>
          </div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🔗</div>
            <div>
              <div className="text-2xl font-bold text-primary">1.2M</div>
              <div className="text-sm text-secondary">Vector Embeddings</div>
            </div>
          </div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🕸️</div>
            <div>
              <div className="text-2xl font-bold text-accent">73%</div>
              <div className="text-sm text-secondary">Knowledge Graph Built</div>
            </div>
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Upload Knowledge</h3>
        </div>
        <div className="p-6">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className="border-2 border-dashed border-custom rounded-lg p-8 text-center hover:border-accent transition-colors"
          >
            <div className="text-3xl mb-4">📁</div>
            <p className="text-primary mb-2">Drag and drop files here, or click to browse</p>
            <p className="text-sm text-secondary mb-4">
              Supports PDF, DOCX, TXT, MD, CSV, JSON
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md,.csv,.json"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isProcessing}
              className="px-6 py-2 bg-accent text-white rounded-md hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? 'Processing...' : 'Select Files'}
            </button>
          </div>

          {/* Upload Progress */}
          {isProcessing && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-primary">Uploading {selectedFiles?.length || 0} file(s)...</span>
                <span className="text-secondary">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-tertiary rounded-full h-2">
                <div
                  className="bg-accent h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Quick Upload Sources */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => handleSourceClick('Company Documents')}
              className="p-4 border border-custom rounded-lg hover:bg-card-hover transition-colors"
            >
              <div className="text-lg mb-2">📄</div>
              <div className="font-medium text-primary">Company Docs</div>
              <div className="text-sm text-secondary">Policies, procedures, manuals</div>
            </button>
            <button
              onClick={() => handleSourceClick('Business Data')}
              className="p-4 border border-custom rounded-lg hover:bg-card-hover transition-colors"
            >
              <div className="text-lg mb-2">💼</div>
              <div className="font-medium text-primary">Business Data</div>
              <div className="text-sm text-secondary">Customer data, analytics</div>
            </button>
            <button
              onClick={() => handleSourceClick('Code Repository')}
              className="p-4 border border-custom rounded-lg hover:bg-card-hover transition-colors"
            >
              <div className="text-lg mb-2">💻</div>
              <div className="font-medium text-primary">Code Repository</div>
              <div className="text-sm text-secondary">Source code, documentation</div>
            </button>
          </div>
        </div>
      </div>

      {/* Knowledge Sources */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Knowledge Sources</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="border-b border-custom">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Documents
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Last Updated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-custom">
              {knowledgeSources.map((source, index) => (
                <tr key={index} className="hover:bg-card-hover transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-primary">{source.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-secondary">{source.type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(source.status)}`}>
                      {source.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                    {source.size}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                    {source.documents}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-tertiary">
                    {source.lastUpdated}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => alert('Coming Soon: Re-process')}
                      className="text-accent hover:text-accent/80 mr-3 transition-colors"
                    >
                      Re-process
                    </button>
                    <button
                      onClick={() => alert('Coming Soon: Remove')}
                      className="text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}