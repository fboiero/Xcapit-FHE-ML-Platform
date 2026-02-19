import { useState } from 'react'
import { useTranslation } from 'react-i18next'

// Report Builder page - Generate custom reports with visualizations
export default function ReportBuilder() {
  const { t } = useTranslation()
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [reportConfig, setReportConfig] = useState({
    title: '',
    description: '',
    dateRange: 'last_30_days',
    sections: [],
    format: 'pdf',
  })
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedReports, setGeneratedReports] = useState([
    {
      id: '1',
      title: 'Monthly Performance Report',
      createdAt: '2026-01-25T10:00:00Z',
      format: 'pdf',
      status: 'completed',
      size: '2.4 MB',
    },
    {
      id: '2',
      title: 'Model Accuracy Analysis',
      createdAt: '2026-01-20T14:30:00Z',
      format: 'xlsx',
      status: 'completed',
      size: '1.1 MB',
    },
    {
      id: '3',
      title: 'Consortium Activity Report',
      createdAt: '2026-01-15T09:15:00Z',
      format: 'pdf',
      status: 'completed',
      size: '3.2 MB',
    },
  ])

  const templates = [
    {
      id: 'performance',
      name: 'Performance Report',
      description: 'Model accuracy, latency, and usage metrics',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      sections: ['overview', 'accuracy_metrics', 'latency_analysis', 'usage_trends'],
    },
    {
      id: 'compliance',
      name: 'Compliance Report',
      description: 'Regulatory compliance and audit trail',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      sections: ['compliance_status', 'audit_logs', 'data_access', 'encryption_status'],
    },
    {
      id: 'consortium',
      name: 'Consortium Report',
      description: 'Member activity and collaboration metrics',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      sections: ['member_overview', 'contribution_metrics', 'voting_history', 'shared_resources'],
    },
    {
      id: 'custom',
      name: 'Custom Report',
      description: 'Build your own report from scratch',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      sections: [],
    },
  ]

  const availableSections = [
    { id: 'overview', name: 'Executive Overview', category: 'general' },
    { id: 'accuracy_metrics', name: 'Accuracy Metrics', category: 'performance' },
    { id: 'latency_analysis', name: 'Latency Analysis', category: 'performance' },
    { id: 'usage_trends', name: 'Usage Trends', category: 'performance' },
    { id: 'compliance_status', name: 'Compliance Status', category: 'compliance' },
    { id: 'audit_logs', name: 'Audit Logs', category: 'compliance' },
    { id: 'data_access', name: 'Data Access History', category: 'compliance' },
    { id: 'encryption_status', name: 'Encryption Status', category: 'security' },
    { id: 'member_overview', name: 'Member Overview', category: 'consortium' },
    { id: 'contribution_metrics', name: 'Contribution Metrics', category: 'consortium' },
    { id: 'voting_history', name: 'Voting History', category: 'consortium' },
    { id: 'shared_resources', name: 'Shared Resources', category: 'consortium' },
    { id: 'model_inventory', name: 'Model Inventory', category: 'models' },
    { id: 'training_history', name: 'Training History', category: 'models' },
    { id: 'prediction_logs', name: 'Prediction Logs', category: 'models' },
  ]

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template)
    setReportConfig({
      ...reportConfig,
      title: template.name,
      sections: template.sections,
    })
  }

  const toggleSection = (sectionId) => {
    setReportConfig({
      ...reportConfig,
      sections: reportConfig.sections.includes(sectionId)
        ? reportConfig.sections.filter((s) => s !== sectionId)
        : [...reportConfig.sections, sectionId],
    })
  }

  const handleGenerate = () => {
    setIsGenerating(true)
    // Simulate report generation
    setTimeout(() => {
      const newReport = {
        id: Date.now().toString(),
        title: reportConfig.title || 'Untitled Report',
        createdAt: new Date().toISOString(),
        format: reportConfig.format,
        status: 'completed',
        size: '1.8 MB',
      }
      setGeneratedReports([newReport, ...generatedReports])
      setIsGenerating(false)
      setSelectedTemplate(null)
      setReportConfig({
        title: '',
        description: '',
        dateRange: 'last_30_days',
        sections: [],
        format: 'pdf',
      })
    }, 3000)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Report Builder</h1>
          <p className="text-gray-500 mt-1">Create custom reports and analytics</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Builder Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Template Selection */}
          {!selectedTemplate && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Choose a Template</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className="flex items-start p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors text-left"
                  >
                    <div className="text-indigo-600 mr-4">{template.icon}</div>
                    <div>
                      <h3 className="font-medium text-gray-900">{template.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">{template.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Report Configuration */}
          {selectedTemplate && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Configure Report</h2>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-6">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Title
                  </label>
                  <input
                    type="text"
                    value={reportConfig.title}
                    onChange={(e) => setReportConfig({ ...reportConfig, title: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter report title"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={reportConfig.description}
                    onChange={(e) => setReportConfig({ ...reportConfig, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    rows={3}
                    placeholder="Optional description"
                  />
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range
                  </label>
                  <select
                    value={reportConfig.dateRange}
                    onChange={(e) => setReportConfig({ ...reportConfig, dateRange: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="last_7_days">Last 7 Days</option>
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_90_days">Last 90 Days</option>
                    <option value="last_year">Last Year</option>
                    <option value="custom">Custom Range</option>
                  </select>
                </div>

                {/* Sections */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Sections
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {availableSections.map((section) => (
                      <label
                        key={section.id}
                        className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                          reportConfig.sections.includes(section.id)
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={reportConfig.sections.includes(section.id)}
                          onChange={() => toggleSection(section.id)}
                          className="sr-only"
                        />
                        <div className={`w-4 h-4 rounded border mr-3 flex items-center justify-center ${
                          reportConfig.sections.includes(section.id)
                            ? 'bg-indigo-600 border-indigo-600'
                            : 'border-gray-300'
                        }`}>
                          {reportConfig.sections.includes(section.id) && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                        <span className="text-sm text-gray-700">{section.name}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Format */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Output Format
                  </label>
                  <div className="flex space-x-4">
                    {['pdf', 'xlsx', 'csv', 'json'].map((format) => (
                      <label
                        key={format}
                        className={`flex items-center px-4 py-2 border rounded-lg cursor-pointer transition-colors ${
                          reportConfig.format === format
                            ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="format"
                          value={format}
                          checked={reportConfig.format === format}
                          onChange={(e) => setReportConfig({ ...reportConfig, format: e.target.value })}
                          className="sr-only"
                        />
                        <span className="text-sm font-medium uppercase">{format}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <div className="flex justify-end">
                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating || reportConfig.sections.length === 0}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Generate Report
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Generated Reports Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Reports</h2>
            <div className="space-y-3">
              {generatedReports.map((report) => (
                <div
                  key={report.id}
                  className="p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {report.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(report.createdAt).toLocaleDateString()} - {report.size}
                      </p>
                    </div>
                    <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded uppercase">
                      {report.format}
                    </span>
                  </div>
                  <div className="flex items-center mt-2 space-x-2">
                    <button className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                      Download
                    </button>
                    <span className="text-gray-300">|</span>
                    <button className="text-xs text-gray-500 hover:text-gray-700">
                      View
                    </button>
                    <span className="text-gray-300">|</span>
                    <button className="text-xs text-red-500 hover:text-red-700">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {generatedReports.length === 0 && (
              <div className="text-center py-8">
                <svg className="w-12 h-12 mx-auto text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-500 mt-2">No reports generated yet</p>
              </div>
            )}
          </div>

          {/* Scheduled Reports */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Scheduled Reports</h2>
            <div className="space-y-3">
              <div className="p-3 border border-gray-100 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Weekly Performance</h3>
                    <p className="text-xs text-gray-500">Every Monday at 9:00 AM</p>
                  </div>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                </div>
              </div>
              <div className="p-3 border border-gray-100 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Monthly Compliance</h3>
                    <p className="text-xs text-gray-500">1st of every month</p>
                  </div>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                </div>
              </div>
            </div>
            <button className="w-full mt-4 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 text-sm">
              + Schedule New Report
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
