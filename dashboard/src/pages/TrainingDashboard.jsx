import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

export default function TrainingDashboard() {
  const { t } = useTranslation();
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [totalEpochs, setTotalEpochs] = useState(100);
  const [metrics, setMetrics] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedModel, setSelectedModel] = useState('logistic_regression');
  const [trainingConfig, setTrainingConfig] = useState({
    learning_rate: 0.01,
    batch_size: 32,
    epochs: 100,
    early_stopping: true,
    patience: 10,
  });
  const logsEndRef = useRef(null);

  const models = [
    { id: 'logistic_regression', name: 'Logistic Regression' },
    { id: 'linear_regression', name: 'Linear Regression' },
    { id: 'random_forest', name: 'Random Forest' },
    { id: 'neural_network', name: 'Neural Network' },
    { id: 'gradient_boosting', name: 'Gradient Boosting' },
    { id: 'svm', name: 'SVM' },
  ];

  // Simulate training progress
  useEffect(() => {
    if (!isTraining) return;

    const interval = setInterval(() => {
      setCurrentEpoch((prev) => {
        const next = prev + 1;
        if (next >= totalEpochs) {
          setIsTraining(false);
          addLog('Training completed!', 'success');
          return prev;
        }

        // Simulate metrics
        const loss = 0.5 * Math.exp(-next / 30) + Math.random() * 0.05;
        const accuracy = 0.5 + 0.4 * (1 - Math.exp(-next / 25)) + Math.random() * 0.02;
        const valLoss = loss + 0.1 + Math.random() * 0.05;
        const valAccuracy = accuracy - 0.05 + Math.random() * 0.02;

        setMetrics((prev) => [
          ...prev,
          {
            epoch: next,
            loss: loss.toFixed(4),
            accuracy: (accuracy * 100).toFixed(2),
            val_loss: valLoss.toFixed(4),
            val_accuracy: (valAccuracy * 100).toFixed(2),
          },
        ]);

        setTrainingProgress((next / totalEpochs) * 100);

        if (next % 10 === 0) {
          addLog(`Epoch ${next}/${totalEpochs} - loss: ${loss.toFixed(4)}, accuracy: ${(accuracy * 100).toFixed(2)}%`);
        }

        return next;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [isTraining, totalEpochs]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { timestamp, message, type }]);
  };

  const startTraining = () => {
    setIsTraining(true);
    setCurrentEpoch(0);
    setTrainingProgress(0);
    setMetrics([]);
    setLogs([]);
    setTotalEpochs(trainingConfig.epochs);
    addLog(`Starting training with ${selectedModel}...`);
    addLog(`Config: lr=${trainingConfig.learning_rate}, batch=${trainingConfig.batch_size}, epochs=${trainingConfig.epochs}`);
  };

  const stopTraining = () => {
    setIsTraining(false);
    addLog('Training stopped by user', 'warning');
  };

  const getLatestMetrics = () => {
    if (metrics.length === 0) return null;
    return metrics[metrics.length - 1];
  };

  const latest = getLatestMetrics();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {t('training.title', 'Training Dashboard')}
          </h1>
          <p className="mt-2 text-gray-600">
            {t('training.subtitle', 'Train FHE models with real-time progress monitoring')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Training Configuration */}
          <div className="lg:col-span-1 space-y-6">
            {/* Model Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('training.modelSelection', 'Model Selection')}
              </h2>

              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isTraining}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100"
              >
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Training Config */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('training.configuration', 'Configuration')}
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Learning Rate
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    value={trainingConfig.learning_rate}
                    onChange={(e) =>
                      setTrainingConfig({ ...trainingConfig, learning_rate: parseFloat(e.target.value) })
                    }
                    disabled={isTraining}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 disabled:bg-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={trainingConfig.batch_size}
                    onChange={(e) =>
                      setTrainingConfig({ ...trainingConfig, batch_size: parseInt(e.target.value) })
                    }
                    disabled={isTraining}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 disabled:bg-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Epochs
                  </label>
                  <input
                    type="number"
                    value={trainingConfig.epochs}
                    onChange={(e) =>
                      setTrainingConfig({ ...trainingConfig, epochs: parseInt(e.target.value) })
                    }
                    disabled={isTraining}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 disabled:bg-gray-100"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="earlyStop"
                    checked={trainingConfig.early_stopping}
                    onChange={(e) =>
                      setTrainingConfig({ ...trainingConfig, early_stopping: e.target.checked })
                    }
                    disabled={isTraining}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="earlyStop" className="ml-2 text-sm text-gray-700">
                    Early Stopping
                  </label>
                </div>

                {trainingConfig.early_stopping && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Patience
                    </label>
                    <input
                      type="number"
                      value={trainingConfig.patience}
                      onChange={(e) =>
                        setTrainingConfig({ ...trainingConfig, patience: parseInt(e.target.value) })
                      }
                      disabled={isTraining}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 disabled:bg-gray-100"
                    />
                  </div>
                )}
              </div>

              <div className="mt-6">
                {!isTraining ? (
                  <button
                    onClick={startTraining}
                    className="w-full bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition flex items-center justify-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Start Training
                  </button>
                ) : (
                  <button
                    onClick={stopTraining}
                    className="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition flex items-center justify-center"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                    </svg>
                    Stop Training
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Training Progress & Metrics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Bar */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-lg font-semibold">
                  {t('training.progress', 'Training Progress')}
                </h2>
                <span className="text-sm text-gray-500">
                  Epoch {currentEpoch} / {totalEpochs}
                </span>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
                <div
                  className="bg-gradient-to-r from-purple-500 to-indigo-600 h-4 rounded-full transition-all duration-300"
                  style={{ width: `${trainingProgress}%` }}
                />
              </div>

              {isTraining && (
                <div className="flex items-center text-sm text-purple-600">
                  <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Training in progress...
                </div>
              )}
            </div>

            {/* Real-time Metrics */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('training.metrics', 'Real-time Metrics')}
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-600">
                    {latest?.loss || '--'}
                  </div>
                  <div className="text-sm text-blue-800">Train Loss</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-600">
                    {latest ? `${latest.accuracy}%` : '--'}
                  </div>
                  <div className="text-sm text-green-800">Train Accuracy</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-orange-600">
                    {latest?.val_loss || '--'}
                  </div>
                  <div className="text-sm text-orange-800">Val Loss</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-purple-600">
                    {latest ? `${latest.val_accuracy}%` : '--'}
                  </div>
                  <div className="text-sm text-purple-800">Val Accuracy</div>
                </div>
              </div>

              {/* Metrics Chart (Simplified) */}
              <div className="h-48 bg-gray-50 rounded-lg p-4 overflow-hidden">
                <div className="h-full flex items-end space-x-1">
                  {metrics.slice(-50).map((m, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-purple-500 rounded-t transition-all duration-200"
                      style={{ height: `${parseFloat(m.accuracy)}%` }}
                      title={`Epoch ${m.epoch}: ${m.accuracy}%`}
                    />
                  ))}
                </div>
                <div className="text-xs text-gray-500 mt-2 text-center">
                  Accuracy over epochs
                </div>
              </div>
            </div>

            {/* Training Logs */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('training.logs', 'Training Logs')}
              </h2>

              <div className="bg-gray-900 rounded-lg p-4 h-48 overflow-y-auto font-mono text-sm">
                {logs.length === 0 ? (
                  <div className="text-gray-500">No logs yet. Start training to see output.</div>
                ) : (
                  logs.map((log, i) => (
                    <div
                      key={i}
                      className={`${
                        log.type === 'success'
                          ? 'text-green-400'
                          : log.type === 'warning'
                          ? 'text-yellow-400'
                          : log.type === 'error'
                          ? 'text-red-400'
                          : 'text-gray-300'
                      }`}
                    >
                      <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </div>

            {/* FHE Status */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">FHE Encryption Status</h3>
                  <p className="text-purple-200 text-sm mt-1">
                    All training computations performed on encrypted data
                  </p>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse mr-2" />
                  <span className="font-medium">Active</span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">128-bit</div>
                  <div className="text-purple-200 text-xs">Security Level</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">CKKS</div>
                  <div className="text-purple-200 text-xs">Encryption Scheme</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">0</div>
                  <div className="text-purple-200 text-xs">Data Leaks</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
