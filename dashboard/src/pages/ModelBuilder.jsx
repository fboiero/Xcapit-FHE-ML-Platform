import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const MODELS = [
  {
    id: 'linear_regression',
    name: 'Linear Regression',
    type: 'regression',
    params: [
      { name: 'learning_rate', type: 'number', default: 0.01, min: 0.001, max: 1, step: 0.001 },
      { name: 'n_epochs', type: 'number', default: 100, min: 10, max: 1000, step: 10 },
    ],
  },
  {
    id: 'logistic_regression',
    name: 'Logistic Regression',
    type: 'classification',
    params: [
      { name: 'learning_rate', type: 'number', default: 0.01, min: 0.001, max: 1, step: 0.001 },
      { name: 'n_epochs', type: 'number', default: 100, min: 10, max: 1000, step: 10 },
    ],
  },
  {
    id: 'decision_tree',
    name: 'Decision Tree',
    type: 'both',
    params: [
      { name: 'max_depth', type: 'number', default: 5, min: 1, max: 20, step: 1 },
      { name: 'min_samples_split', type: 'number', default: 2, min: 2, max: 20, step: 1 },
    ],
  },
  {
    id: 'random_forest',
    name: 'Random Forest',
    type: 'both',
    params: [
      { name: 'n_estimators', type: 'number', default: 10, min: 5, max: 100, step: 5 },
      { name: 'max_depth', type: 'number', default: 5, min: 1, max: 20, step: 1 },
      { name: 'max_features', type: 'select', default: 'sqrt', options: ['sqrt', 'log2', 'all'] },
    ],
  },
  {
    id: 'gradient_boosting',
    name: 'Gradient Boosting',
    type: 'both',
    params: [
      { name: 'n_estimators', type: 'number', default: 100, min: 10, max: 500, step: 10 },
      { name: 'max_depth', type: 'number', default: 3, min: 1, max: 10, step: 1 },
      { name: 'learning_rate', type: 'number', default: 0.1, min: 0.01, max: 1, step: 0.01 },
    ],
  },
  {
    id: 'neural_network',
    name: 'Neural Network',
    type: 'both',
    params: [
      { name: 'hidden_layers', type: 'text', default: '32,16', placeholder: 'e.g. 64,32,16' },
      { name: 'learning_rate', type: 'number', default: 0.01, min: 0.001, max: 1, step: 0.001 },
      { name: 'n_epochs', type: 'number', default: 100, min: 10, max: 500, step: 10 },
      { name: 'activation', type: 'select', default: 'polynomial_sigmoid', options: ['square', 'polynomial_sigmoid', 'polynomial_tanh'] },
    ],
  },
  {
    id: 'svm',
    name: 'SVM',
    type: 'both',
    params: [
      { name: 'C', type: 'number', default: 1.0, min: 0.1, max: 100, step: 0.1 },
      { name: 'kernel', type: 'select', default: 'polynomial', options: ['linear', 'polynomial', 'quadratic'] },
      { name: 'degree', type: 'number', default: 2, min: 1, max: 5, step: 1 },
    ],
  },
  {
    id: 'naive_bayes',
    name: 'Gaussian Naive Bayes',
    type: 'classification',
    params: [
      { name: 'var_smoothing', type: 'number', default: 1e-9, min: 1e-12, max: 1e-6, step: 1e-10 },
    ],
  },
  {
    id: 'kmeans',
    name: 'K-Means',
    type: 'clustering',
    params: [
      { name: 'n_clusters', type: 'number', default: 3, min: 2, max: 20, step: 1 },
      { name: 'max_iter', type: 'number', default: 100, min: 10, max: 500, step: 10 },
      { name: 'init', type: 'select', default: 'kmeans++', options: ['kmeans++', 'random'] },
    ],
  },
  {
    id: 'pca',
    name: 'PCA',
    type: 'dimensionality',
    params: [
      { name: 'n_components', type: 'number', default: 2, min: 1, max: 50, step: 1 },
      { name: 'whiten', type: 'checkbox', default: false },
    ],
  },
];

const MODEL_TYPES = [
  { id: 'all', label: 'All' },
  { id: 'classification', label: 'Classification' },
  { id: 'regression', label: 'Regression' },
  { id: 'clustering', label: 'Clustering' },
  { id: 'dimensionality', label: 'Dimensionality Reduction' },
];

export default function ModelBuilder() {
  const { t } = useTranslation();
  const [selectedType, setSelectedType] = useState('all');
  const [selectedModel, setSelectedModel] = useState(null);
  const [params, setParams] = useState({});
  const [generatedCode, setGeneratedCode] = useState('');

  const filteredModels = MODELS.filter(
    (m) => selectedType === 'all' || m.type === selectedType || m.type === 'both'
  );

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    const defaultParams = {};
    model.params.forEach((p) => {
      defaultParams[p.name] = p.default;
    });
    setParams(defaultParams);
    setGeneratedCode('');
  };

  const handleParamChange = (name, value) => {
    setParams((prev) => ({ ...prev, [name]: value }));
  };

  const generateCode = () => {
    if (!selectedModel) return;

    const modelName = selectedModel.name.replace(/\s/g, '');
    const paramsStr = Object.entries(params)
      .map(([k, v]) => {
        if (typeof v === 'string' && !v.match(/^[\d.]+$/)) {
          return `    ${k}="${v}"`;
        }
        return `    ${k}=${v}`;
      })
      .join(',\n');

    const code = `from xcapit_fhe import ${modelName}

# Create model
model = ${modelName}(
${paramsStr}
)

# Train on data
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate
score = model.score(X_test, y_test)
print(f"Score: {score:.4f}")
`;

    setGeneratedCode(code);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {t('modelBuilder.title', 'FHE Model Builder')}
          </h1>
          <p className="mt-2 text-gray-600">
            {t('modelBuilder.subtitle', 'Configure and generate code for FHE-compatible ML models')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Model Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              {t('modelBuilder.selectModel', 'Select Model')}
            </h2>

            {/* Type Filter */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('modelBuilder.filterByType', 'Filter by Type')}
              </label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
              >
                {MODEL_TYPES.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Model List */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredModels.map((model) => (
                <button
                  key={model.id}
                  onClick={() => handleModelSelect(model)}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                    selectedModel?.id === model.id
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium">{model.name}</div>
                  <div className="text-xs text-gray-500 capitalize">{model.type}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Parameters */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              {t('modelBuilder.parameters', 'Parameters')}
            </h2>

            {selectedModel ? (
              <div className="space-y-4">
                {selectedModel.params.map((param) => (
                  <div key={param.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {param.name}
                    </label>

                    {param.type === 'number' && (
                      <input
                        type="number"
                        value={params[param.name] || param.default}
                        onChange={(e) => handleParamChange(param.name, parseFloat(e.target.value))}
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
                      />
                    )}

                    {param.type === 'text' && (
                      <input
                        type="text"
                        value={params[param.name] || param.default}
                        onChange={(e) => handleParamChange(param.name, e.target.value)}
                        placeholder={param.placeholder}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
                      />
                    )}

                    {param.type === 'select' && (
                      <select
                        value={params[param.name] || param.default}
                        onChange={(e) => handleParamChange(param.name, e.target.value)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
                      >
                        {param.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    )}

                    {param.type === 'checkbox' && (
                      <input
                        type="checkbox"
                        checked={params[param.name] || param.default}
                        onChange={(e) => handleParamChange(param.name, e.target.checked)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                    )}
                  </div>
                ))}

                <button
                  onClick={generateCode}
                  className="w-full mt-4 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors"
                >
                  {t('modelBuilder.generateCode', 'Generate Code')}
                </button>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                {t('modelBuilder.selectModelPrompt', 'Select a model to configure parameters')}
              </div>
            )}
          </div>

          {/* Generated Code */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              {t('modelBuilder.generatedCode', 'Generated Code')}
            </h2>

            {generatedCode ? (
              <div className="relative">
                <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{generatedCode}</code>
                </pre>
                <button
                  onClick={() => navigator.clipboard.writeText(generatedCode)}
                  className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded text-xs hover:bg-gray-600"
                >
                  {t('modelBuilder.copy', 'Copy')}
                </button>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8 bg-gray-50 rounded-lg">
                {t('modelBuilder.codeWillAppear', 'Generated code will appear here')}
              </div>
            )}

            {selectedModel && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-2">
                  {t('modelBuilder.fheNotes', 'FHE Compatibility Notes')}
                </h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Training is done on plaintext data</li>
                  <li>• Predictions work on encrypted data</li>
                  <li>• Uses polynomial approximations for FHE</li>
                  <li>• Security: 128-bit encryption by default</li>
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Model Comparison */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            {t('modelBuilder.modelComparison', 'Model Comparison')}
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">FHE Depth</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Speed</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accuracy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr>
                  <td className="px-4 py-3 text-sm font-medium">Linear/Logistic Regression</td>
                  <td className="px-4 py-3 text-sm">Linear</td>
                  <td className="px-4 py-3 text-sm"><span className="text-green-600">Low (1)</span></td>
                  <td className="px-4 py-3 text-sm"><span className="text-green-600">Fast</span></td>
                  <td className="px-4 py-3 text-sm">Good for linear data</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium">Decision Tree</td>
                  <td className="px-4 py-3 text-sm">Tree</td>
                  <td className="px-4 py-3 text-sm"><span className="text-yellow-600">Medium (2-3)</span></td>
                  <td className="px-4 py-3 text-sm"><span className="text-green-600">Fast</span></td>
                  <td className="px-4 py-3 text-sm">Good for non-linear</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium">Random Forest</td>
                  <td className="px-4 py-3 text-sm">Ensemble</td>
                  <td className="px-4 py-3 text-sm"><span className="text-yellow-600">Medium (2-3)</span></td>
                  <td className="px-4 py-3 text-sm"><span className="text-yellow-600">Medium</span></td>
                  <td className="px-4 py-3 text-sm">Very good</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium">Neural Network</td>
                  <td className="px-4 py-3 text-sm">Deep Learning</td>
                  <td className="px-4 py-3 text-sm"><span className="text-red-600">High (4+)</span></td>
                  <td className="px-4 py-3 text-sm"><span className="text-red-600">Slow</span></td>
                  <td className="px-4 py-3 text-sm">Excellent</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium">Naive Bayes</td>
                  <td className="px-4 py-3 text-sm">Probabilistic</td>
                  <td className="px-4 py-3 text-sm"><span className="text-green-600">Low (1)</span></td>
                  <td className="px-4 py-3 text-sm"><span className="text-green-600">Very Fast</span></td>
                  <td className="px-4 py-3 text-sm">Good for text</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
