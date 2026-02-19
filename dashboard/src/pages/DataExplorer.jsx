import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

export default function DataExplorer() {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [columns, setColumns] = useState([])
  const [selectedColumn, setSelectedColumn] = useState(null)
  const [stats, setStats] = useState({})
  const [filterValue, setFilterValue] = useState('')
  const [sortColumn, setSortColumn] = useState(null)
  const [sortDirection, setSortDirection] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)

  // Generate sample data on mount
  useEffect(() => {
    const sampleData = generateSampleData(200)
    setData(sampleData.rows)
    setColumns(sampleData.columns)
    computeStats(sampleData.rows, sampleData.columns)
  }, [])

  const generateSampleData = (n) => {
    const cols = ['id', 'age', 'income', 'score', 'category', 'region', 'active']
    const categories = ['A', 'B', 'C', 'D']
    const regions = ['North', 'South', 'East', 'West']

    const rows = Array.from({ length: n }, (_, i) => ({
      id: i + 1,
      age: Math.floor(Math.random() * 50) + 20,
      income: Math.floor(Math.random() * 100000) + 30000,
      score: Math.round((Math.random() * 100) * 10) / 10,
      category: categories[Math.floor(Math.random() * categories.length)],
      region: regions[Math.floor(Math.random() * regions.length)],
      active: Math.random() > 0.3,
    }))

    return { rows, columns: cols }
  }

  const computeStats = (rows, cols) => {
    const newStats = {}
    cols.forEach(col => {
      const values = rows.map(r => r[col]).filter(v => v !== null && v !== undefined)
      const numericValues = values.filter(v => typeof v === 'number')

      if (numericValues.length > 0) {
        newStats[col] = {
          type: 'numeric',
          count: values.length,
          missing: rows.length - values.length,
          mean: numericValues.reduce((a, b) => a + b, 0) / numericValues.length,
          min: Math.min(...numericValues),
          max: Math.max(...numericValues),
          std: Math.sqrt(
            numericValues.reduce((sq, n) => sq + Math.pow(n - (numericValues.reduce((a, b) => a + b, 0) / numericValues.length), 2), 0) / numericValues.length
          ),
        }
      } else if (typeof values[0] === 'boolean') {
        const trueCount = values.filter(v => v === true).length
        newStats[col] = {
          type: 'boolean',
          count: values.length,
          trueCount,
          falseCount: values.length - trueCount,
          truePercent: (trueCount / values.length) * 100,
        }
      } else {
        const uniqueValues = [...new Set(values)]
        const valueCounts = {}
        values.forEach(v => { valueCounts[v] = (valueCounts[v] || 0) + 1 })
        newStats[col] = {
          type: 'categorical',
          count: values.length,
          unique: uniqueValues.length,
          topValues: Object.entries(valueCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5),
        }
      }
    })
    setStats(newStats)
  }

  const filteredData = useMemo(() => {
    if (!data) return []
    let result = data

    if (filterValue) {
      result = result.filter(row =>
        Object.values(row).some(val =>
          String(val).toLowerCase().includes(filterValue.toLowerCase())
        )
      )
    }

    if (sortColumn) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortColumn]
        const bVal = b[sortColumn]
        const direction = sortDirection === 'asc' ? 1 : -1
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return (aVal - bVal) * direction
        }
        return String(aVal).localeCompare(String(bVal)) * direction
      })
    }

    return result
  }, [data, filterValue, sortColumn, sortDirection])

  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filteredData.slice(start, start + pageSize)
  }, [filteredData, currentPage, pageSize])

  const totalPages = Math.ceil(filteredData.length / pageSize)

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const renderHistogram = (values, bins = 10) => {
    const numericValues = values.filter(v => typeof v === 'number')
    if (numericValues.length === 0) return null

    const min = Math.min(...numericValues)
    const max = Math.max(...numericValues)
    const binWidth = (max - min) / bins
    const histogram = new Array(bins).fill(0)

    numericValues.forEach(v => {
      const binIndex = Math.min(Math.floor((v - min) / binWidth), bins - 1)
      histogram[binIndex]++
    })

    const maxCount = Math.max(...histogram)

    return (
      <div className="flex items-end space-x-1 h-24">
        {histogram.map((count, i) => (
          <div
            key={i}
            className="flex-1 bg-brand-500 rounded-t hover:bg-brand-600 transition-colors"
            style={{ height: `${(count / maxCount) * 100}%` }}
            title={`${(min + i * binWidth).toFixed(1)} - ${(min + (i + 1) * binWidth).toFixed(1)}: ${count}`}
          />
        ))}
      </div>
    )
  }

  const renderBarChart = (topValues) => {
    const maxCount = Math.max(...topValues.map(([, count]) => count))

    return (
      <div className="space-y-2">
        {topValues.map(([value, count]) => (
          <div key={value} className="flex items-center">
            <span className="w-16 text-xs text-slate-600 truncate">{value}</span>
            <div className="flex-1 mx-2 h-4 bg-slate-100 rounded overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded"
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
            </div>
            <span className="text-xs text-slate-500">{count}</span>
          </div>
        ))}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('dataExplorer.title')}</h1>
          <p className="text-slate-600 mt-1">{t('dataExplorer.subtitle')}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-white border border-slate-200 rounded-lg px-4 py-2">
            <span className="text-sm text-slate-500">{t('dataExplorer.rows')}: </span>
            <span className="font-semibold text-slate-900">{data.length}</span>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg px-4 py-2">
            <span className="text-sm text-slate-500">{t('dataExplorer.columns')}: </span>
            <span className="font-semibold text-slate-900">{columns.length}</span>
          </div>
        </div>
      </div>

      {/* Column Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {columns.map(col => (
          <div
            key={col}
            className={`bg-white rounded-xl border p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedColumn === col ? 'border-brand-500 ring-2 ring-brand-100' : 'border-slate-200'
            }`}
            onClick={() => setSelectedColumn(selectedColumn === col ? null : col)}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-slate-900">{col}</h3>
              <span className={`text-xs px-2 py-1 rounded-full ${
                stats[col]?.type === 'numeric' ? 'bg-blue-100 text-blue-700' :
                stats[col]?.type === 'boolean' ? 'bg-green-100 text-green-700' :
                'bg-purple-100 text-purple-700'
              }`}>
                {stats[col]?.type}
              </span>
            </div>

            {stats[col]?.type === 'numeric' && (
              <>
                <div className="mb-3">
                  {renderHistogram(data.map(r => r[col]))}
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-slate-500">{t('dataExplorer.mean')}: </span>
                    <span className="font-medium">{stats[col].mean.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">{t('dataExplorer.std')}: </span>
                    <span className="font-medium">{stats[col].std.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">{t('dataExplorer.min')}: </span>
                    <span className="font-medium">{stats[col].min.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">{t('dataExplorer.max')}: </span>
                    <span className="font-medium">{stats[col].max.toFixed(2)}</span>
                  </div>
                </div>
              </>
            )}

            {stats[col]?.type === 'boolean' && (
              <div className="space-y-2">
                <div className="flex h-4 rounded-full overflow-hidden bg-slate-100">
                  <div
                    className="bg-green-500"
                    style={{ width: `${stats[col].truePercent}%` }}
                  />
                  <div
                    className="bg-red-400"
                    style={{ width: `${100 - stats[col].truePercent}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">True: {stats[col].trueCount}</span>
                  <span className="text-red-500">False: {stats[col].falseCount}</span>
                </div>
              </div>
            )}

            {stats[col]?.type === 'categorical' && (
              <>
                <p className="text-sm text-slate-500 mb-2">
                  {stats[col].unique} {t('dataExplorer.uniqueValues')}
                </p>
                {renderBarChart(stats[col].topValues)}
              </>
            )}
          </div>
        ))}
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">{t('dataExplorer.dataPreview')}</h2>
          <input
            type="text"
            placeholder={t('dataExplorer.filterPlaceholder')}
            value={filterValue}
            onChange={(e) => setFilterValue(e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {columns.map(col => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left text-sm font-medium text-slate-600 cursor-pointer hover:bg-slate-100"
                    onClick={() => handleSort(col)}
                  >
                    <div className="flex items-center gap-1">
                      {col}
                      {sortColumn === col && (
                        <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, idx) => (
                <tr key={idx} className="border-t border-slate-100 hover:bg-slate-50">
                  {columns.map(col => (
                    <td key={col} className="px-4 py-3 text-sm text-slate-700">
                      {typeof row[col] === 'boolean' ? (
                        <span className={`px-2 py-1 rounded text-xs ${row[col] ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {row[col] ? 'True' : 'False'}
                        </span>
                      ) : (
                        String(row[col])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-200 flex items-center justify-between">
          <span className="text-sm text-slate-500">
            {t('dataExplorer.showing')} {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, filteredData.length)} {t('dataExplorer.of')} {filteredData.length}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-50 hover:bg-slate-50"
            >
              {t('dataExplorer.previous')}
            </button>
            <span className="text-sm text-slate-600">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-50 hover:bg-slate-50"
            >
              {t('dataExplorer.next')}
            </button>
          </div>
        </div>
      </div>

      {/* Correlation Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="font-semibold text-slate-900 mb-4">{t('dataExplorer.correlationMatrix')}</h2>
        <CorrelationMatrix data={data} columns={columns.filter(c => stats[c]?.type === 'numeric')} />
      </div>
    </div>
  )
}

function CorrelationMatrix({ data, columns }) {
  const correlations = useMemo(() => {
    const matrix = {}
    columns.forEach(col1 => {
      matrix[col1] = {}
      columns.forEach(col2 => {
        const values1 = data.map(r => r[col1])
        const values2 = data.map(r => r[col2])
        matrix[col1][col2] = pearsonCorrelation(values1, values2)
      })
    })
    return matrix
  }, [data, columns])

  const pearsonCorrelation = (x, y) => {
    const n = x.length
    const meanX = x.reduce((a, b) => a + b, 0) / n
    const meanY = y.reduce((a, b) => a + b, 0) / n
    const numerator = x.reduce((sum, xi, i) => sum + (xi - meanX) * (y[i] - meanY), 0)
    const denomX = Math.sqrt(x.reduce((sum, xi) => sum + Math.pow(xi - meanX, 2), 0))
    const denomY = Math.sqrt(y.reduce((sum, yi) => sum + Math.pow(yi - meanY, 2), 0))
    return numerator / (denomX * denomY)
  }

  const getColor = (value) => {
    if (value >= 0.7) return 'bg-green-500'
    if (value >= 0.4) return 'bg-green-300'
    if (value >= 0) return 'bg-green-100'
    if (value >= -0.4) return 'bg-red-100'
    if (value >= -0.7) return 'bg-red-300'
    return 'bg-red-500'
  }

  return (
    <div className="overflow-x-auto">
      <table className="text-sm">
        <thead>
          <tr>
            <th className="p-2"></th>
            {columns.map(col => (
              <th key={col} className="p-2 font-medium text-slate-600 text-center">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {columns.map(col1 => (
            <tr key={col1}>
              <td className="p-2 font-medium text-slate-600">{col1}</td>
              {columns.map(col2 => (
                <td key={col2} className="p-1">
                  <div
                    className={`w-12 h-12 flex items-center justify-center rounded ${getColor(correlations[col1][col2])} ${
                      col1 === col2 ? 'bg-slate-200' : ''
                    }`}
                    title={`${col1} vs ${col2}: ${correlations[col1][col2].toFixed(3)}`}
                  >
                    <span className="text-xs font-medium text-slate-700">
                      {correlations[col1][col2].toFixed(2)}
                    </span>
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
