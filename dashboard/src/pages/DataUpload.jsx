import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';

export default function DataUpload() {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [columns, setColumns] = useState([]);
  const [targetColumn, setTargetColumn] = useState('');
  const [featureColumns, setFeatureColumns] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dataStats, setDataStats] = useState(null);

  const handleFileSelect = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploadStatus('processing');

    try {
      const text = await selectedFile.text();
      const lines = text.trim().split('\n');
      const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));

      setColumns(headers);
      setFeatureColumns(headers.slice(0, -1));
      setTargetColumn(headers[headers.length - 1]);

      // Parse data for preview
      const data = lines.slice(1, 6).map((line) => {
        const values = line.split(',').map((v) => v.trim().replace(/"/g, ''));
        const row = {};
        headers.forEach((h, i) => {
          row[h] = values[i];
        });
        return row;
      });

      setPreview(data);

      // Calculate basic stats
      const allData = lines.slice(1).map((line) =>
        line.split(',').map((v) => parseFloat(v.trim().replace(/"/g, '')))
      );

      const stats = {
        rows: allData.length,
        columns: headers.length,
        numericColumns: headers.filter((_, i) =>
          allData.every((row) => !isNaN(row[i]))
        ).length,
        missingValues: allData.reduce((acc, row) =>
          acc + row.filter((v) => isNaN(v) || v === null || v === '').length, 0
        ),
      };

      setDataStats(stats);
      setUploadStatus('ready');
    } catch (error) {
      console.error('Error parsing file:', error);
      setUploadStatus('error');
    }
  };

  const handleFeatureToggle = (column) => {
    if (column === targetColumn) return;

    setFeatureColumns((prev) => {
      if (prev.includes(column)) {
        return prev.filter((c) => c !== column);
      }
      return [...prev, column];
    });
  };

  const handleTargetSelect = (column) => {
    setTargetColumn(column);
    setFeatureColumns((prev) => prev.filter((c) => c !== column));
  };

  const generateEncryptionCode = () => {
    if (!file || !targetColumn) return '';

    return `from xcapit_fhe import SecureDataLoader, create_standard_pipeline
import pandas as pd

# Load data
df = pd.read_csv("${file.name}")

# Define features and target
features = ${JSON.stringify(featureColumns)}
target = "${targetColumn}"

X = df[features].values
y = df[target].values

# Preprocess data
pipeline = create_standard_pipeline(
    handle_missing=True,
    scaling='minmax'  # Best for FHE
)
X_processed = pipeline.fit_transform(X)

# Encrypt data
loader = SecureDataLoader(
    security_level=128,
    normalize=False  # Already preprocessed
)
encrypted_data = loader.encrypt(X_processed, y)

print(f"Encrypted {len(X)} samples")
print(f"Features: {len(features)}")
print(f"Encryption complete!")
`;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {t('dataUpload.title', 'Data Upload & Encryption')}
          </h1>
          <p className="mt-2 text-gray-600">
            {t('dataUpload.subtitle', 'Upload your dataset and prepare it for FHE encryption')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <div className="space-y-6">
            {/* File Upload */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('dataUpload.uploadFile', 'Upload File')}
              </h2>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-purple-500 transition-colors"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.tsv"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>

                <p className="mt-2 text-sm text-gray-600">
                  {file
                    ? file.name
                    : t('dataUpload.dropzone', 'Click to upload or drag and drop')}
                </p>
                <p className="text-xs text-gray-500">CSV files only</p>
              </div>

              {uploadStatus === 'processing' && (
                <div className="mt-4 flex items-center text-blue-600">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
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
                  Processing file...
                </div>
              )}

              {uploadStatus === 'error' && (
                <div className="mt-4 text-red-600">
                  Error processing file. Please ensure it&apos;s a valid CSV.
                </div>
              )}
            </div>

            {/* Data Stats */}
            {dataStats && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">
                  {t('dataUpload.dataStats', 'Data Statistics')}
                </h2>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{dataStats.rows}</div>
                    <div className="text-sm text-blue-800">Rows</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">{dataStats.columns}</div>
                    <div className="text-sm text-green-800">Columns</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">{dataStats.numericColumns}</div>
                    <div className="text-sm text-purple-800">Numeric Columns</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-yellow-600">{dataStats.missingValues}</div>
                    <div className="text-sm text-yellow-800">Missing Values</div>
                  </div>
                </div>
              </div>
            )}

            {/* Column Selection */}
            {columns.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">
                  {t('dataUpload.selectColumns', 'Select Columns')}
                </h2>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Column (y)
                  </label>
                  <select
                    value={targetColumn}
                    onChange={(e) => handleTargetSelect(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    {columns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Feature Columns (X)
                  </label>
                  <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-2">
                    {columns
                      .filter((col) => col !== targetColumn)
                      .map((col) => (
                        <label
                          key={col}
                          className="flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={featureColumns.includes(col)}
                            onChange={() => handleFeatureToggle(col)}
                            className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm">{col}</span>
                        </label>
                      ))}
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    {featureColumns.length} features selected
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Preview and Code */}
          <div className="space-y-6">
            {/* Data Preview */}
            {preview && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">
                  {t('dataUpload.preview', 'Data Preview')}
                </h2>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        {columns.map((col) => (
                          <th
                            key={col}
                            className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                              col === targetColumn
                                ? 'bg-purple-100 text-purple-800'
                                : featureColumns.includes(col)
                                ? 'bg-blue-50 text-blue-800'
                                : 'bg-gray-50 text-gray-500'
                            }`}
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {preview.map((row, i) => (
                        <tr key={i}>
                          {columns.map((col) => (
                            <td key={col} className="px-3 py-2 text-sm text-gray-900">
                              {row[col]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-2 text-xs text-gray-500">
                  Showing first 5 rows
                </div>
              </div>
            )}

            {/* Generated Code */}
            {file && targetColumn && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">
                  {t('dataUpload.encryptionCode', 'Encryption Code')}
                </h2>

                <div className="relative">
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm max-h-96">
                    <code>{generateEncryptionCode()}</code>
                  </pre>
                  <button
                    onClick={() => navigator.clipboard.writeText(generateEncryptionCode())}
                    className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded text-xs hover:bg-gray-600"
                  >
                    Copy
                  </button>
                </div>
              </div>
            )}

            {/* FHE Info */}
            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg shadow p-6 text-white">
              <h2 className="text-lg font-semibold mb-4">
                {t('dataUpload.fheInfo', 'About FHE Encryption')}
              </h2>

              <ul className="space-y-3 text-sm">
                <li className="flex items-start">
                  <svg className="h-5 w-5 mr-2 text-purple-200" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Data remains encrypted during all ML computations</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 mr-2 text-purple-200" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>128-bit security (NSA approved)</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 mr-2 text-purple-200" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Only you have the decryption key</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 mr-2 text-purple-200" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>GDPR and HIPAA compliant</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
