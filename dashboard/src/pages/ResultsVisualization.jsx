import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function ResultsVisualization() {
  const { t } = useTranslation();
  const [selectedModel, setSelectedModel] = useState('model_1');
  const [selectedMetric, setSelectedMetric] = useState('confusion');

  // Simulated model results
  const modelResults = {
    model_1: {
      name: 'Logistic Regression v1.2',
      accuracy: 0.92,
      precision: 0.89,
      recall: 0.94,
      f1: 0.91,
      auc: 0.96,
      confusionMatrix: [
        [850, 50],
        [30, 70],
      ],
      rocCurve: generateROCData(0.96),
      precisionRecallCurve: generatePRData(0.91),
      featureImportance: [
        { name: 'transaction_amount', importance: 0.32 },
        { name: 'time_since_last', importance: 0.25 },
        { name: 'merchant_category', importance: 0.18 },
        { name: 'device_type', importance: 0.12 },
        { name: 'location_risk', importance: 0.08 },
        { name: 'other', importance: 0.05 },
      ],
    },
    model_2: {
      name: 'Random Forest v2.0',
      accuracy: 0.94,
      precision: 0.91,
      recall: 0.93,
      f1: 0.92,
      auc: 0.97,
      confusionMatrix: [
        [860, 40],
        [25, 75],
      ],
      rocCurve: generateROCData(0.97),
      precisionRecallCurve: generatePRData(0.92),
      featureImportance: [
        { name: 'transaction_amount', importance: 0.28 },
        { name: 'time_since_last', importance: 0.22 },
        { name: 'merchant_category', importance: 0.20 },
        { name: 'device_type', importance: 0.15 },
        { name: 'location_risk', importance: 0.10 },
        { name: 'other', importance: 0.05 },
      ],
    },
  };

  function generateROCData(auc) {
    const points = [];
    for (let i = 0; i <= 100; i++) {
      const fpr = i / 100;
      // Simulate ROC curve with given AUC
      const tpr = Math.pow(fpr, 1 / (2 * auc - 1));
      points.push({ fpr, tpr });
    }
    return points;
  }

  function generatePRData(f1) {
    const points = [];
    for (let i = 0; i <= 100; i++) {
      const recall = i / 100;
      // Simulate PR curve
      const precision = f1 * 2 / (recall + f1 + 0.1);
      points.push({ recall, precision: Math.min(1, precision) });
    }
    return points;
  }

  const currentModel = modelResults[selectedModel];

  const renderConfusionMatrix = () => {
    const cm = currentModel.confusionMatrix;
    const total = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1];

    return (
      <div className="flex flex-col items-center">
        <div className="text-sm text-gray-500 mb-2">Predicted</div>
        <div className="flex">
          <div className="flex flex-col justify-center mr-2">
            <div className="text-sm text-gray-500 transform -rotate-90 origin-center whitespace-nowrap">
              Actual
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1">
            <div className="w-24 h-24 bg-green-100 flex flex-col items-center justify-center rounded-lg border-2 border-green-500">
              <span className="text-2xl font-bold text-green-700">{cm[0][0]}</span>
              <span className="text-xs text-green-600">TN</span>
              <span className="text-xs text-gray-500">{((cm[0][0] / total) * 100).toFixed(1)}%</span>
            </div>
            <div className="w-24 h-24 bg-red-100 flex flex-col items-center justify-center rounded-lg border-2 border-red-300">
              <span className="text-2xl font-bold text-red-600">{cm[0][1]}</span>
              <span className="text-xs text-red-600">FP</span>
              <span className="text-xs text-gray-500">{((cm[0][1] / total) * 100).toFixed(1)}%</span>
            </div>
            <div className="w-24 h-24 bg-red-100 flex flex-col items-center justify-center rounded-lg border-2 border-red-300">
              <span className="text-2xl font-bold text-red-600">{cm[1][0]}</span>
              <span className="text-xs text-red-600">FN</span>
              <span className="text-xs text-gray-500">{((cm[1][0] / total) * 100).toFixed(1)}%</span>
            </div>
            <div className="w-24 h-24 bg-green-100 flex flex-col items-center justify-center rounded-lg border-2 border-green-500">
              <span className="text-2xl font-bold text-green-700">{cm[1][1]}</span>
              <span className="text-xs text-green-600">TP</span>
              <span className="text-xs text-gray-500">{((cm[1][1] / total) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
        <div className="flex mt-4 text-xs text-gray-500 space-x-4">
          <span>Negative (0)</span>
          <span>|</span>
          <span>Positive (1)</span>
        </div>
      </div>
    );
  };

  const renderROCCurve = () => {
    const data = currentModel.rocCurve;
    const width = 300;
    const height = 300;
    const padding = 40;

    const points = data
      .map((p) => {
        const x = padding + p.fpr * (width - 2 * padding);
        const y = height - padding - p.tpr * (height - 2 * padding);
        return `${x},${y}`;
      })
      .join(' ');

    return (
      <svg width={width} height={height} className="mx-auto">
        {/* Background */}
        <rect x={padding} y={padding} width={width - 2 * padding} height={height - 2 * padding} fill="#f9fafb" />

        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((v) => (
          <g key={v}>
            <line
              x1={padding + v * (width - 2 * padding)}
              y1={padding}
              x2={padding + v * (width - 2 * padding)}
              y2={height - padding}
              stroke="#e5e7eb"
              strokeDasharray="4"
            />
            <line
              x1={padding}
              y1={height - padding - v * (height - 2 * padding)}
              x2={width - padding}
              y2={height - padding - v * (height - 2 * padding)}
              stroke="#e5e7eb"
              strokeDasharray="4"
            />
          </g>
        ))}

        {/* Diagonal line (random classifier) */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={padding} stroke="#9ca3af" strokeDasharray="4" />

        {/* ROC curve */}
        <polyline points={points} fill="none" stroke="#8b5cf6" strokeWidth="3" />

        {/* Fill under curve */}
        <polygon
          points={`${padding},${height - padding} ${points} ${width - padding},${height - padding}`}
          fill="rgba(139, 92, 246, 0.2)"
        />

        {/* Axes */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#374151" strokeWidth="2" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#374151" strokeWidth="2" />

        {/* Labels */}
        <text x={width / 2} y={height - 5} textAnchor="middle" className="text-xs fill-gray-600">
          False Positive Rate
        </text>
        <text x={15} y={height / 2} textAnchor="middle" transform={`rotate(-90, 15, ${height / 2})`} className="text-xs fill-gray-600">
          True Positive Rate
        </text>

        {/* AUC label */}
        <text x={width - padding - 10} y={padding + 20} textAnchor="end" className="text-sm font-bold fill-purple-600">
          AUC = {currentModel.auc.toFixed(3)}
        </text>
      </svg>
    );
  };

  const renderFeatureImportance = () => {
    const data = currentModel.featureImportance;
    const maxImportance = Math.max(...data.map((d) => d.importance));

    return (
      <div className="space-y-3">
        {data.map((feature, i) => (
          <div key={feature.name}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-700">{feature.name}</span>
              <span className="text-gray-500">{(feature.importance * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="h-3 rounded-full transition-all duration-500"
                style={{
                  width: `${(feature.importance / maxImportance) * 100}%`,
                  backgroundColor: `hsl(${260 - i * 20}, 70%, 50%)`,
                }}
              />
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
            {t('results.title', 'Results Visualization')}
          </h1>
          <p className="mt-2 text-gray-600">
            {t('results.subtitle', 'Analyze model performance with interactive visualizations')}
          </p>
        </div>

        {/* Model Selector */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Select Model:</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
              >
                {Object.entries(modelResults).map(([id, model]) => (
                  <option key={id} value={id}>
                    {model.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-2">
              {['confusion', 'roc', 'features'].map((metric) => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                    selectedMetric === metric
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {metric === 'confusion' ? 'Confusion Matrix' : metric === 'roc' ? 'ROC Curve' : 'Feature Importance'}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Metrics Cards */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Performance Metrics</h2>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Accuracy</span>
                  <span className="text-xl font-bold text-green-600">
                    {(currentModel.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${currentModel.accuracy * 100}%` }}
                  />
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Precision</span>
                  <span className="text-xl font-bold text-blue-600">
                    {(currentModel.precision * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${currentModel.precision * 100}%` }}
                  />
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Recall</span>
                  <span className="text-xl font-bold text-orange-600">
                    {(currentModel.recall * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${currentModel.recall * 100}%` }}
                  />
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600">F1 Score</span>
                  <span className="text-xl font-bold text-purple-600">
                    {(currentModel.f1 * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${currentModel.f1 * 100}%` }}
                  />
                </div>

                <div className="flex justify-between items-center pt-2 border-t">
                  <span className="text-gray-600">ROC AUC</span>
                  <span className="text-xl font-bold text-indigo-600">
                    {currentModel.auc.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>

            {/* Classification Report */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Classification Report</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Class</th>
                      <th className="text-right py-2">Precision</th>
                      <th className="text-right py-2">Recall</th>
                      <th className="text-right py-2">F1</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="py-2">Negative (0)</td>
                      <td className="text-right">{(currentModel.precision * 0.95).toFixed(2)}</td>
                      <td className="text-right">{(currentModel.recall * 1.02).toFixed(2)}</td>
                      <td className="text-right">{(currentModel.f1 * 0.98).toFixed(2)}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2">Positive (1)</td>
                      <td className="text-right">{currentModel.precision.toFixed(2)}</td>
                      <td className="text-right">{currentModel.recall.toFixed(2)}</td>
                      <td className="text-right">{currentModel.f1.toFixed(2)}</td>
                    </tr>
                    <tr className="font-semibold">
                      <td className="py-2">Weighted Avg</td>
                      <td className="text-right">{currentModel.precision.toFixed(2)}</td>
                      <td className="text-right">{currentModel.recall.toFixed(2)}</td>
                      <td className="text-right">{currentModel.f1.toFixed(2)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Main Visualization */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-6">
                {selectedMetric === 'confusion'
                  ? 'Confusion Matrix'
                  : selectedMetric === 'roc'
                  ? 'ROC Curve'
                  : 'Feature Importance'}
              </h2>

              <div className="flex justify-center">
                {selectedMetric === 'confusion' && renderConfusionMatrix()}
                {selectedMetric === 'roc' && renderROCCurve()}
                {selectedMetric === 'features' && (
                  <div className="w-full max-w-md">
                    {renderFeatureImportance()}
                  </div>
                )}
              </div>

              {/* Interpretation */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Interpretation</h3>
                {selectedMetric === 'confusion' && (
                  <p className="text-sm text-gray-600">
                    The confusion matrix shows {currentModel.confusionMatrix[0][0] + currentModel.confusionMatrix[1][1]} correct predictions
                    out of {currentModel.confusionMatrix.flat().reduce((a, b) => a + b, 0)} total samples.
                    The model has a low false positive rate ({currentModel.confusionMatrix[0][1]} FP) and
                    false negative rate ({currentModel.confusionMatrix[1][0]} FN).
                  </p>
                )}
                {selectedMetric === 'roc' && (
                  <p className="text-sm text-gray-600">
                    The ROC curve with AUC = {currentModel.auc.toFixed(3)} indicates excellent classification performance.
                    An AUC close to 1.0 means the model has strong discriminative ability between positive and negative classes.
                    The curve is well above the diagonal (random classifier baseline).
                  </p>
                )}
                {selectedMetric === 'features' && (
                  <p className="text-sm text-gray-600">
                    The top contributing features are transaction_amount ({(currentModel.featureImportance[0].importance * 100).toFixed(1)}%)
                    and time_since_last ({(currentModel.featureImportance[1].importance * 100).toFixed(1)}%).
                    These features have the highest predictive power for the target variable.
                  </p>
                )}
              </div>
            </div>

            {/* Export Options */}
            <div className="mt-4 bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Export Results</span>
                <div className="space-x-2">
                  <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                    Export CSV
                  </button>
                  <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                    Export JSON
                  </button>
                  <button className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700">
                    Generate Report
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
