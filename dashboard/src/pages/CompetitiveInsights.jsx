import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

export default function CompetitiveInsights() {
  const { consortiumId } = useParams()
  const [activeTab, setActiveTab] = useState('benchmarks')
  const [loading, setLoading] = useState(true)
  const [selectedIndustry, setSelectedIndustry] = useState('finance')
  const [benchmarks, setBenchmarks] = useState([])
  const [comparison, setComparison] = useState(null)
  const [trends, setTrends] = useState([])
  const [position, setPosition] = useState(null)
  const [showCompareModal, setShowCompareModal] = useState(false)

  const industries = ['finance', 'healthcare', 'retail']

  useEffect(() => {
    loadData()
  }, [selectedIndustry])

  const loadData = () => {
    setLoading(true)
    setTimeout(() => {
      // Mock benchmarks
      const industryBenchmarks = {
        finance: [
          { metric_name: 'model_accuracy', metric_type: 'accuracy', percentile_10: 0.82, percentile_25: 0.86, percentile_50: 0.89, percentile_75: 0.92, percentile_90: 0.95, sample_size: 127 },
          { metric_name: 'fraud_detection_rate', metric_type: 'accuracy', percentile_10: 0.75, percentile_25: 0.82, percentile_50: 0.87, percentile_75: 0.91, percentile_90: 0.94, sample_size: 98 },
          { metric_name: 'false_positive_rate', metric_type: 'error', percentile_10: 0.02, percentile_25: 0.04, percentile_50: 0.06, percentile_75: 0.10, percentile_90: 0.15, sample_size: 112 },
          { metric_name: 'prediction_latency_ms', metric_type: 'latency', percentile_10: 15, percentile_25: 25, percentile_50: 50, percentile_75: 100, percentile_90: 200, sample_size: 145 },
          { metric_name: 'data_quality_score', metric_type: 'quality', percentile_10: 0.70, percentile_25: 0.78, percentile_50: 0.85, percentile_75: 0.90, percentile_90: 0.95, sample_size: 89 },
        ],
        healthcare: [
          { metric_name: 'diagnostic_accuracy', metric_type: 'accuracy', percentile_10: 0.85, percentile_25: 0.88, percentile_50: 0.91, percentile_75: 0.94, percentile_90: 0.97, sample_size: 76 },
          { metric_name: 'patient_outcome_prediction', metric_type: 'accuracy', percentile_10: 0.72, percentile_25: 0.78, percentile_50: 0.83, percentile_75: 0.88, percentile_90: 0.92, sample_size: 54 },
          { metric_name: 'hipaa_compliance_score', metric_type: 'compliance', percentile_10: 0.90, percentile_25: 0.94, percentile_50: 0.97, percentile_75: 0.99, percentile_90: 1.00, sample_size: 82 },
        ],
        retail: [
          { metric_name: 'demand_forecast_accuracy', metric_type: 'accuracy', percentile_10: 0.78, percentile_25: 0.83, percentile_50: 0.87, percentile_75: 0.91, percentile_90: 0.94, sample_size: 134 },
          { metric_name: 'customer_churn_prediction', metric_type: 'accuracy', percentile_10: 0.70, percentile_25: 0.76, percentile_50: 0.82, percentile_75: 0.87, percentile_90: 0.91, sample_size: 108 },
          { metric_name: 'recommendation_ctr', metric_type: 'engagement', percentile_10: 0.02, percentile_25: 0.04, percentile_50: 0.06, percentile_75: 0.09, percentile_90: 0.12, sample_size: 156 },
        ]
      }
      setBenchmarks(industryBenchmarks[selectedIndustry] || [])

      // Mock comparison
      setComparison({
        overall_percentile: 78,
        comparisons: [
          { metric_name: 'model_accuracy', your_value: 0.91, industry_median: 0.89, percentile_rank: 75, vs_median: 'above' },
          { metric_name: 'fraud_detection_rate', your_value: 0.89, industry_median: 0.87, percentile_rank: 75, vs_median: 'above' },
          { metric_name: 'false_positive_rate', your_value: 0.05, industry_median: 0.06, percentile_rank: 75, vs_median: 'below' },
          { metric_name: 'prediction_latency_ms', your_value: 75, industry_median: 50, percentile_rank: 50, vs_median: 'above' },
          { metric_name: 'data_quality_score', your_value: 0.92, industry_median: 0.85, percentile_rank: 90, vs_median: 'above' },
        ],
        strengths: ['model_accuracy', 'data_quality_score'],
        areas_for_improvement: ['prediction_latency_ms']
      })

      // Mock trends
      setTrends([
        { metric_name: 'model_accuracy', trend_direction: 'improving', change_percentage: 8.5 },
        { metric_name: 'prediction_latency', trend_direction: 'improving', change_percentage: 12.3 },
        { metric_name: 'data_quality', trend_direction: 'improving', change_percentage: 5.2 },
        { metric_name: 'compliance_score', trend_direction: 'stable', change_percentage: 0.8 },
      ])

      // Mock position
      setPosition({
        overall_ranking: 'top_quartile',
        percentile: 78,
        key_strengths: ['model_accuracy', 'data_quality_score', 'fraud_detection_rate'],
        improvement_areas: ['prediction_latency_ms'],
        recommendations: [
          'Focus on reducing prediction latency to reach top decile',
          'Your accuracy is above industry median - consider contributing to more consortiums',
          'Data quality is a competitive advantage'
        ]
      })

      setLoading(false)
    }, 600)
  }

  const getPercentileColor = (percentile) => {
    if (percentile >= 90) return 'text-green-600 bg-green-100'
    if (percentile >= 75) return 'text-blue-600 bg-blue-100'
    if (percentile >= 50) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const formatValue = (value, type) => {
    if (type === 'latency') return `${value}ms`
    if (type === 'percentage' || value <= 1) return `${(value * 100).toFixed(1)}%`
    return value.toFixed(2)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-teal-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">Competitive Insights</h1>
              <p className="mt-2 text-cyan-100">
                Anonymous benchmarks vs industry - see how you compare
              </p>
            </div>
            <button
              onClick={() => setShowCompareModal(true)}
              className="bg-white text-cyan-600 px-4 py-2 rounded-lg font-medium hover:bg-cyan-50 transition-colors"
            >
              Run Comparison
            </button>
          </div>

          {/* Industry Selector */}
          <div className="mt-6 flex gap-2">
            {industries.map(ind => (
              <button
                key={ind}
                onClick={() => setSelectedIndustry(ind)}
                className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${
                  selectedIndustry === ind
                    ? 'bg-white text-cyan-600'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                {ind}
              </button>
            ))}
          </div>

          {/* Position Summary */}
          {position && (
            <div className="mt-6 grid grid-cols-4 gap-4">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{position.percentile}th</div>
                <div className="text-cyan-200">Overall Percentile</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-xl font-bold capitalize">{position.overall_ranking.replace('_', ' ')}</div>
                <div className="text-cyan-200">Industry Ranking</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{position.key_strengths.length}</div>
                <div className="text-cyan-200">Key Strengths</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{position.improvement_areas.length}</div>
                <div className="text-cyan-200">Areas to Improve</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Privacy Banner */}
      <div className="bg-cyan-50 border-b border-cyan-100">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-cyan-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-sm font-medium">
              All benchmarks computed from encrypted aggregate data - individual company data is never exposed
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="border-b border-gray-200">
          <nav className="flex gap-8">
            {[
              { id: 'benchmarks', label: 'Industry Benchmarks' },
              { id: 'comparison', label: 'Your Comparison' },
              { id: 'trends', label: 'Trends' },
              { id: 'recommendations', label: 'Recommendations' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-cyan-600 text-cyan-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Benchmarks Tab */}
        {activeTab === 'benchmarks' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">{selectedIndustry.charAt(0).toUpperCase() + selectedIndustry.slice(1)} Industry Benchmarks</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 font-medium">Metric</th>
                      <th className="pb-3 font-medium text-center">P10</th>
                      <th className="pb-3 font-medium text-center">P25</th>
                      <th className="pb-3 font-medium text-center">Median</th>
                      <th className="pb-3 font-medium text-center">P75</th>
                      <th className="pb-3 font-medium text-center">P90</th>
                      <th className="pb-3 font-medium text-center">Sample</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarks.map((b) => (
                      <tr key={b.metric_name} className="border-b last:border-0">
                        <td className="py-4">
                          <div className="font-medium">{b.metric_name.replace(/_/g, ' ')}</div>
                          <div className="text-xs text-gray-500 capitalize">{b.metric_type}</div>
                        </td>
                        <td className="py-4 text-center text-gray-500">{formatValue(b.percentile_10, b.metric_type)}</td>
                        <td className="py-4 text-center text-gray-600">{formatValue(b.percentile_25, b.metric_type)}</td>
                        <td className="py-4 text-center font-semibold">{formatValue(b.percentile_50, b.metric_type)}</td>
                        <td className="py-4 text-center text-gray-600">{formatValue(b.percentile_75, b.metric_type)}</td>
                        <td className="py-4 text-center text-gray-500">{formatValue(b.percentile_90, b.metric_type)}</td>
                        <td className="py-4 text-center text-sm text-gray-400">{b.sample_size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Visual Benchmark Chart */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Percentile Distribution</h2>
              <div className="space-y-4">
                {benchmarks.filter(b => b.metric_type === 'accuracy').map(b => (
                  <div key={b.metric_name} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{b.metric_name.replace(/_/g, ' ')}</span>
                      <span className="text-gray-500">Median: {formatValue(b.percentile_50, b.metric_type)}</span>
                    </div>
                    <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
                      {/* P10-P90 range */}
                      <div
                        className="absolute h-full bg-gray-200 rounded-full"
                        style={{
                          left: `${b.percentile_10 * 100}%`,
                          width: `${(b.percentile_90 - b.percentile_10) * 100}%`
                        }}
                      />
                      {/* P25-P75 range */}
                      <div
                        className="absolute h-full bg-cyan-200 rounded-full"
                        style={{
                          left: `${b.percentile_25 * 100}%`,
                          width: `${(b.percentile_75 - b.percentile_25) * 100}%`
                        }}
                      />
                      {/* Median line */}
                      <div
                        className="absolute h-full w-1 bg-cyan-600"
                        style={{ left: `${b.percentile_50 * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && comparison && (
          <div className="space-y-6">
            {/* Overall Score */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Your Overall Performance</h2>
                  <p className="text-gray-500">Compared to {selectedIndustry} industry</p>
                </div>
                <div className="text-center">
                  <div className={`text-4xl font-bold ${getPercentileColor(comparison.overall_percentile).split(' ')[0]}`}>
                    {comparison.overall_percentile}th
                  </div>
                  <div className="text-sm text-gray-500">Percentile</div>
                </div>
              </div>
            </div>

            {/* Metric Comparisons */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Metric-by-Metric Comparison</h2>
              <div className="space-y-4">
                {comparison.comparisons.map((c) => (
                  <div key={c.metric_name} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{c.metric_name.replace(/_/g, ' ')}</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(c.percentile_rank)}`}>
                        {c.percentile_rank}th percentile
                      </span>
                    </div>
                    <div className="flex items-center gap-8 text-sm">
                      <div>
                        <span className="text-gray-500">Your Value:</span>
                        <span className="ml-2 font-semibold">{c.your_value}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Industry Median:</span>
                        <span className="ml-2">{c.industry_median}</span>
                      </div>
                      <div className={c.vs_median === 'above' ? 'text-green-600' : 'text-red-600'}>
                        {c.vs_median === 'above' ? 'Above' : 'Below'} median
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths and Improvements */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-green-600 mb-4">Strengths</h3>
                <div className="space-y-2">
                  {comparison.strengths.map(s => (
                    <div key={s} className="flex items-center gap-2 p-2 bg-green-50 rounded">
                      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{s.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-orange-600 mb-4">Areas for Improvement</h3>
                <div className="space-y-2">
                  {comparison.areas_for_improvement.map(a => (
                    <div key={a} className="flex items-center gap-2 p-2 bg-orange-50 rounded">
                      <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      <span>{a.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">{selectedIndustry.charAt(0).toUpperCase() + selectedIndustry.slice(1)} Industry Trends (Quarterly)</h2>
              <div className="grid grid-cols-2 gap-4">
                {trends.map(t => (
                  <div key={t.metric_name} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{t.metric_name.replace(/_/g, ' ')}</span>
                      <div className={`flex items-center gap-1 ${
                        t.trend_direction === 'improving' ? 'text-green-600' :
                        t.trend_direction === 'declining' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {t.trend_direction === 'improving' && (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        )}
                        {t.trend_direction === 'declining' && (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                          </svg>
                        )}
                        <span className="font-semibold">
                          {t.change_percentage > 0 ? '+' : ''}{t.change_percentage}%
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-gray-500 capitalize">
                      {t.trend_direction}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && position && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Strategic Recommendations</h2>
              <div className="space-y-4">
                {position.recommendations.map((rec, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-4 bg-cyan-50 rounded-lg">
                    <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 text-cyan-600 rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </div>
                    <p className="text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Leverage Your Strengths</h2>
              <div className="flex flex-wrap gap-2">
                {position.key_strengths.map(s => (
                  <span key={s} className="px-4 py-2 bg-green-100 text-green-700 rounded-full font-medium">
                    {s.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Compare Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Run Industry Comparison</h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Industry
                </label>
                <select
                  value={selectedIndustry}
                  onChange={(e) => setSelectedIndustry(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-cyan-500"
                >
                  {industries.map(ind => (
                    <option key={ind} value={ind}>{ind.charAt(0).toUpperCase() + ind.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="p-3 bg-cyan-50 rounded-lg text-sm text-cyan-700">
                Your metrics will be compared against anonymized industry benchmarks.
                No individual company data will be exposed.
              </div>
            </div>
            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-xl">
              <button
                onClick={() => setShowCompareModal(false)}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowCompareModal(false)
                  loadData()
                }}
                className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
              >
                Run Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
