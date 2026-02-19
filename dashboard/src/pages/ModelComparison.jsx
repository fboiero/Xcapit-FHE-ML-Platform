import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function ModelComparison() {
  const { t } = useTranslation();
  const [selectedModels, setSelectedModels] = useState(['model_1', 'model_2', 'model_3']);
  const [sortBy, setSortBy] = useState('accuracy');
  const [sortOrder, setSortOrder] = useState('desc');

  const allModels = {
    model_1: {
      id: 'model_1',
      name: 'Logistic Regression',
      version: 'v1.2',
      accuracy: 0.92,
      precision: 0.89,
      recall: 0.94,
      f1: 0.91,
      auc: 0.96,
      trainingTime: '2.3s',
      inferenceTime: '0.5ms',
      fheCompatible: true,
      complexity: 'Low',
      parameters: 156,
      createdAt: '2024-01-15',
    },
    model_2: {
      id: 'model_2',
      name: 'Random Forest',
      version: 'v2.0',
      accuracy: 0.94,
      precision: 0.91,
      recall: 0.93,
      f1: 0.92,
      auc: 0.97,
      trainingTime: '15.2s',
      inferenceTime: '2.1ms',
      fheCompatible: true,
      complexity: 'Medium',
      parameters: 12450,
      createdAt: '2024-01-18',
    },
    model_3: {
      id: 'model_3',
      name: 'Neural Network',
      version: 'v1.0',
      accuracy: 0.95,
      precision: 0.93,
      recall: 0.92,
      f1: 0.925,
      auc: 0.98,
      trainingTime: '45.8s',
      inferenceTime: '5.2ms',
      fheCompatible: true,
      complexity: 'High',
      parameters: 85320,
      createdAt: '2024-01-20',
    },
    model_4: {
      id: 'model_4',
      name: 'Gradient Boosting',
      version: 'v1.5',
      accuracy: 0.93,
      precision: 0.90,
      recall: 0.91,
      f1: 0.905,
      auc: 0.965,
      trainingTime: '28.4s',
      inferenceTime: '3.8ms',
      fheCompatible: true,
      complexity: 'Medium-High',
      parameters: 25600,
      createdAt: '2024-01-22',
    },
    model_5: {
      id: 'model_5',
      name: 'SVM (Polynomial)',
      version: 'v1.1',
      accuracy: 0.91,
      precision: 0.88,
      recall: 0.93,
      f1: 0.904,
      auc: 0.95,
      trainingTime: '8.6s',
      inferenceTime: '1.2ms',
      fheCompatible: true,
      complexity: 'Medium',
      parameters: 2340,
      createdAt: '2024-01-25',
    },
  };

  const handleModelToggle = (modelId) => {
    setSelectedModels((prev) => {
      if (prev.includes(modelId)) {
        return prev.filter((id) => id !== modelId);
      }
      return [...prev, modelId];
    });
  };

  const getSelectedModelData = () => {
    return selectedModels.map((id) => allModels[id]).filter(Boolean);
  };

  const getSortedModels = () => {
    const models = getSelectedModelData();
    return [...models].sort((a, b) => {
      const aVal = typeof a[sortBy] === 'string' ? a[sortBy] : parseFloat(a[sortBy]);
      const bVal = typeof b[sortBy] === 'string' ? b[sortBy] : parseFloat(b[sortBy]);
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      }
      return aVal < bVal ? 1 : -1;
    });
  };

  const getBestModel = (metric) => {
    const models = getSelectedModelData();
    if (models.length === 0) return null;
    return models.reduce((best, current) => {
      return current[metric] > best[metric] ? current : best;
    });
  };

  const getMetricColor = (value, metric) => {
    const best = getBestModel(metric);
    if (!best) return 'text-gray-900';
    if (value === best[metric]) return 'text-green-600 font-bold';
    return 'text-gray-900';
  };

  const renderRadarChart = () => {
    const models = getSelectedModelData();
    if (models.length === 0) return null;

    const metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc'];
    const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
    const center = 150;
    const maxRadius = 100;
    const angleStep = (2 * Math.PI) / metrics.length;

    const getPoint = (value, index) => {
      const angle = index * angleStep - Math.PI / 2;
      const radius = value * maxRadius;
      return {
        x: center + radius * Math.cos(angle),
        y: center + radius * Math.sin(angle),
      };
    };

    return (
      <svg width="300" height="300" className="mx-auto">
        {/* Background circles */}
        {[0.2, 0.4, 0.6, 0.8, 1].map((scale) => (
          <circle
            key={scale}
            cx={center}
            cy={center}
            r={scale * maxRadius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}

        {/* Axes */}
        {metrics.map((_, i) => {
          const point = getPoint(1, i);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={point.x}
              y2={point.y}
              stroke="#d1d5db"
              strokeWidth="1"
            />
          );
        })}

        {/* Metric labels */}
        {metrics.map((metric, i) => {
          const point = getPoint(1.2, i);
          return (
            <text
              key={metric}
              x={point.x}
              y={point.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-xs fill-gray-600 capitalize"
            >
              {metric}
            </text>
          );
        })}

        {/* Model polygons */}
        {models.map((model, modelIdx) => {
          const points = metrics.map((metric, i) => {
            const point = getPoint(model[metric], i);
            return `${point.x},${point.y}`;
          }).join(' ');

          return (
            <g key={model.id}>
              <polygon
                points={points}
                fill={colors[modelIdx % colors.length]}
                fillOpacity="0.2"
                stroke={colors[modelIdx % colors.length]}
                strokeWidth="2"
              />
              {metrics.map((metric, i) => {
                const point = getPoint(model[metric], i);
                return (
                  <circle
                    key={i}
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill={colors[modelIdx % colors.length]}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>
    );
  };

  const renderBarChart = (metric) => {
    const models = getSelectedModelData();
    const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
    const maxValue = Math.max(...models.map((m) => m[metric]));

    return (
      <div className="space-y-2">
        {models.map((model, i) => (
          <div key={model.id} className="flex items-center">
            <div className="w-32 text-sm text-gray-600 truncate">{model.name}</div>
            <div className="flex-1 mx-2">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="h-4 rounded-full transition-all duration-500"
                  style={{
                    width: `${(model[metric] / maxValue) * 100}%`,
                    backgroundColor: colors[i % colors.length],
                  }}
                />
              </div>
            </div>
            <div className="w-16 text-right text-sm font-medium">
              {typeof model[metric] === 'number'
                ? (model[metric] * 100).toFixed(1) + '%'
                : model[metric]}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {t('comparison.title', 'Model Comparison')}
          </h1>
          <p className="mt-2 text-gray-600">
            {t('comparison.subtitle', 'Compare multiple FHE models side-by-side')}
          </p>
        </div>

        {/* Model Selection */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Select Models to Compare</h2>
          <div className="flex flex-wrap gap-3">
            {Object.values(allModels).map((model) => (
              <button
                key={model.id}
                onClick={() => handleModelToggle(model.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  selectedModels.includes(model.id)
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {model.name} {model.version}
              </button>
            ))}
          </div>
        </div>

        {selectedModels.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">Select at least one model to compare</p>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
              {['accuracy', 'precision', 'recall', 'f1', 'auc'].map((metric) => {
                const best = getBestModel(metric);
                return (
                  <div key={metric} className="bg-white rounded-lg shadow p-4">
                    <div className="text-sm text-gray-500 capitalize mb-1">Best {metric}</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {best ? (best[metric] * 100).toFixed(1) + '%' : '--'}
                    </div>
                    <div className="text-xs text-gray-400">{best?.name}</div>
                  </div>
                );
              })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Radar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Performance Overview</h2>
                {renderRadarChart()}
                <div className="flex flex-wrap justify-center gap-4 mt-4">
                  {getSelectedModelData().map((model, i) => {
                    const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
                    return (
                      <div key={model.id} className="flex items-center">
                        <div
                          className="w-3 h-3 rounded-full mr-2"
                          style={{ backgroundColor: colors[i % colors.length] }}
                        />
                        <span className="text-sm text-gray-600">{model.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Bar Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold">Metric Comparison</h2>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="border border-gray-300 rounded-md px-2 py-1 text-sm"
                  >
                    <option value="accuracy">Accuracy</option>
                    <option value="precision">Precision</option>
                    <option value="recall">Recall</option>
                    <option value="f1">F1 Score</option>
                    <option value="auc">AUC</option>
                  </select>
                </div>
                {renderBarChart(sortBy)}
              </div>
            </div>

            {/* Comparison Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold">Detailed Comparison</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Model
                      </th>
                      <th
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700"
                        onClick={() => {
                          setSortBy('accuracy');
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        }}
                      >
                        Accuracy {sortBy === 'accuracy' && (sortOrder === 'asc' ? '↑' : '↓')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Precision
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Recall
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        F1
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        AUC
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Training
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Inference
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        FHE
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getSortedModels().map((model) => (
                      <tr key={model.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{model.name}</div>
                          <div className="text-xs text-gray-500">{model.version}</div>
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap ${getMetricColor(model.accuracy, 'accuracy')}`}>
                          {(model.accuracy * 100).toFixed(1)}%
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap ${getMetricColor(model.precision, 'precision')}`}>
                          {(model.precision * 100).toFixed(1)}%
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap ${getMetricColor(model.recall, 'recall')}`}>
                          {(model.recall * 100).toFixed(1)}%
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap ${getMetricColor(model.f1, 'f1')}`}>
                          {(model.f1 * 100).toFixed(1)}%
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap ${getMetricColor(model.auc, 'auc')}`}>
                          {model.auc.toFixed(3)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                          {model.trainingTime}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                          {model.inferenceTime}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {model.fheCompatible ? (
                            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                              Compatible
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                              Not Compatible
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg shadow p-6 text-white">
              <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Best Overall</div>
                  <div className="text-xl font-bold">{getBestModel('accuracy')?.name}</div>
                  <div className="text-purple-200 text-xs mt-1">
                    Highest accuracy with good balance across metrics
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Fastest Inference</div>
                  <div className="text-xl font-bold">
                    {getSelectedModelData().reduce((a, b) =>
                      parseFloat(a.inferenceTime) < parseFloat(b.inferenceTime) ? a : b
                    ).name}
                  </div>
                  <div className="text-purple-200 text-xs mt-1">
                    Best for real-time predictions
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Best Recall</div>
                  <div className="text-xl font-bold">{getBestModel('recall')?.name}</div>
                  <div className="text-purple-200 text-xs mt-1">
                    Minimizes false negatives
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
