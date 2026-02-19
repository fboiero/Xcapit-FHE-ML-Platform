import { useState } from 'react'
import { useTranslation } from 'react-i18next'

// Workflow Automation page - Visual pipeline builder
export default function WorkflowAutomation() {
  const { t } = useTranslation()
  const [workflows, setWorkflows] = useState([
    {
      id: '1',
      name: 'Daily Model Retraining',
      description: 'Automatically retrain models with new data daily',
      status: 'active',
      lastRun: '2026-01-27T06:00:00Z',
      nextRun: '2026-01-28T06:00:00Z',
      steps: 4,
      successRate: 98.5,
    },
    {
      id: '2',
      name: 'Data Quality Check',
      description: 'Validate incoming data before processing',
      status: 'active',
      lastRun: '2026-01-27T08:30:00Z',
      nextRun: '2026-01-27T09:30:00Z',
      steps: 3,
      successRate: 100,
    },
    {
      id: '3',
      name: 'Weekly Report Generation',
      description: 'Generate and distribute weekly analytics reports',
      status: 'paused',
      lastRun: '2026-01-20T09:00:00Z',
      nextRun: null,
      steps: 5,
      successRate: 95.2,
    },
  ])

  const [showEditor, setShowEditor] = useState(false)
  const [editingWorkflow, setEditingWorkflow] = useState(null)
  const [workflowConfig, setWorkflowConfig] = useState({
    name: '',
    description: '',
    trigger: 'schedule',
    schedule: 'daily',
    steps: [],
  })

  const availableSteps = [
    {
      id: 'data_fetch',
      name: 'Fetch Data',
      category: 'input',
      icon: '📥',
      description: 'Retrieve data from source',
    },
    {
      id: 'data_validate',
      name: 'Validate Data',
      category: 'transform',
      icon: '✅',
      description: 'Check data quality and schema',
    },
    {
      id: 'data_transform',
      name: 'Transform Data',
      category: 'transform',
      icon: '🔄',
      description: 'Apply transformations',
    },
    {
      id: 'encrypt',
      name: 'Encrypt Data',
      category: 'security',
      icon: '🔐',
      description: 'Apply FHE encryption',
    },
    {
      id: 'train_model',
      name: 'Train Model',
      category: 'ml',
      icon: '🧠',
      description: 'Train or retrain ML model',
    },
    {
      id: 'evaluate',
      name: 'Evaluate Model',
      category: 'ml',
      icon: '📊',
      description: 'Calculate metrics',
    },
    {
      id: 'predict',
      name: 'Run Predictions',
      category: 'ml',
      icon: '🎯',
      description: 'Generate predictions',
    },
    {
      id: 'notify',
      name: 'Send Notification',
      category: 'output',
      icon: '📧',
      description: 'Email or webhook notification',
    },
    {
      id: 'export',
      name: 'Export Results',
      category: 'output',
      icon: '📤',
      description: 'Save to file or API',
    },
    {
      id: 'condition',
      name: 'Conditional',
      category: 'logic',
      icon: '❓',
      description: 'Branch based on condition',
    },
  ]

  const runHistory = [
    { id: '1', workflow: 'Daily Model Retraining', status: 'success', startTime: '2026-01-27T06:00:00Z', duration: '12m 34s' },
    { id: '2', workflow: 'Data Quality Check', status: 'success', startTime: '2026-01-27T08:30:00Z', duration: '2m 15s' },
    { id: '3', workflow: 'Daily Model Retraining', status: 'success', startTime: '2026-01-26T06:00:00Z', duration: '11m 52s' },
    { id: '4', workflow: 'Weekly Report Generation', status: 'failed', startTime: '2026-01-20T09:00:00Z', duration: '5m 22s' },
    { id: '5', workflow: 'Data Quality Check', status: 'success', startTime: '2026-01-27T07:30:00Z', duration: '2m 08s' },
  ]

  const addStep = (step) => {
    setWorkflowConfig({
      ...workflowConfig,
      steps: [...workflowConfig.steps, { ...step, id: Date.now().toString() }],
    })
  }

  const removeStep = (stepId) => {
    setWorkflowConfig({
      ...workflowConfig,
      steps: workflowConfig.steps.filter((s) => s.id !== stepId),
    })
  }

  const moveStep = (index, direction) => {
    const newSteps = [...workflowConfig.steps]
    const newIndex = index + direction
    if (newIndex >= 0 && newIndex < newSteps.length) {
      [newSteps[index], newSteps[newIndex]] = [newSteps[newIndex], newSteps[index]]
      setWorkflowConfig({ ...workflowConfig, steps: newSteps })
    }
  }

  const saveWorkflow = () => {
    const newWorkflow = {
      id: editingWorkflow?.id || Date.now().toString(),
      name: workflowConfig.name,
      description: workflowConfig.description,
      status: 'active',
      lastRun: null,
      nextRun: new Date(Date.now() + 86400000).toISOString(),
      steps: workflowConfig.steps.length,
      successRate: 100,
    }

    if (editingWorkflow) {
      setWorkflows(workflows.map((w) => (w.id === editingWorkflow.id ? newWorkflow : w)))
    } else {
      setWorkflows([newWorkflow, ...workflows])
    }

    setShowEditor(false)
    setEditingWorkflow(null)
    setWorkflowConfig({ name: '', description: '', trigger: 'schedule', schedule: 'daily', steps: [] })
  }

  const toggleWorkflowStatus = (id) => {
    setWorkflows(
      workflows.map((w) =>
        w.id === id ? { ...w, status: w.status === 'active' ? 'paused' : 'active' } : w
      )
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflow Automation</h1>
          <p className="text-gray-500 mt-1">Create and manage automated pipelines</p>
        </div>
        <button
          onClick={() => setShowEditor(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Workflow
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Total Workflows</p>
              <p className="text-2xl font-bold text-gray-900">{workflows.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {workflows.filter((w) => w.status === 'active').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Runs Today</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">97.8%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Editor Modal */}
      {showEditor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold text-gray-900">
                {editingWorkflow ? 'Edit Workflow' : 'Create Workflow'}
              </h2>
              <button
                onClick={() => {
                  setShowEditor(false)
                  setEditingWorkflow(null)
                  setWorkflowConfig({ name: '', description: '', trigger: 'schedule', schedule: 'daily', steps: [] })
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left: Config */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Workflow Name
                    </label>
                    <input
                      type="text"
                      value={workflowConfig.name}
                      onChange={(e) => setWorkflowConfig({ ...workflowConfig, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      placeholder="My Workflow"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      value={workflowConfig.description}
                      onChange={(e) => setWorkflowConfig({ ...workflowConfig, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      rows={2}
                      placeholder="What does this workflow do?"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Trigger
                    </label>
                    <select
                      value={workflowConfig.trigger}
                      onChange={(e) => setWorkflowConfig({ ...workflowConfig, trigger: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="schedule">Schedule</option>
                      <option value="webhook">Webhook</option>
                      <option value="event">Event</option>
                      <option value="manual">Manual</option>
                    </select>
                  </div>

                  {workflowConfig.trigger === 'schedule' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Schedule
                      </label>
                      <select
                        value={workflowConfig.schedule}
                        onChange={(e) => setWorkflowConfig({ ...workflowConfig, schedule: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="hourly">Every Hour</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="cron">Custom (Cron)</option>
                      </select>
                    </div>
                  )}

                  {/* Available Steps */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Available Steps
                    </label>
                    <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                      {availableSteps.map((step) => (
                        <button
                          key={step.id}
                          onClick={() => addStep(step)}
                          className="flex items-center p-2 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 text-left"
                        >
                          <span className="text-xl mr-2">{step.icon}</span>
                          <span className="text-sm text-gray-700">{step.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right: Pipeline View */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Pipeline Steps ({workflowConfig.steps.length})
                  </label>
                  <div className="bg-gray-50 rounded-lg p-4 min-h-[300px]">
                    {workflowConfig.steps.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        <p>Add steps from the left panel</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {workflowConfig.steps.map((step, index) => (
                          <div
                            key={step.id}
                            className="flex items-center bg-white p-3 rounded-lg border border-gray-200"
                          >
                            <span className="text-xl mr-3">{step.icon}</span>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">{step.name}</p>
                              <p className="text-xs text-gray-500">{step.description}</p>
                            </div>
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => moveStep(index, -1)}
                                disabled={index === 0}
                                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                </svg>
                              </button>
                              <button
                                onClick={() => moveStep(index, 1)}
                                disabled={index === workflowConfig.steps.length - 1}
                                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                              </button>
                              <button
                                onClick={() => removeStep(step.id)}
                                className="p-1 text-red-400 hover:text-red-600"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end p-6 border-t bg-gray-50">
              <button
                onClick={() => setShowEditor(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 mr-2"
              >
                Cancel
              </button>
              <button
                onClick={saveWorkflow}
                disabled={!workflowConfig.name || workflowConfig.steps.length === 0}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Save Workflow
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflows List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Your Workflows</h2>
        </div>
        <div className="divide-y">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-4 ${
                    workflow.status === 'active' ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{workflow.name}</h3>
                    <p className="text-sm text-gray-500">{workflow.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Success Rate</p>
                    <p className="text-lg font-semibold text-gray-900">{workflow.successRate}%</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => toggleWorkflowStatus(workflow.id)}
                      className={`px-3 py-1 rounded-lg text-sm font-medium ${
                        workflow.status === 'active'
                          ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      }`}
                    >
                      {workflow.status === 'active' ? 'Pause' : 'Resume'}
                    </button>
                    <button className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-200">
                      Run Now
                    </button>
                    <button className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200">
                      Edit
                    </button>
                  </div>
                </div>
              </div>
              <div className="mt-4 flex items-center text-sm text-gray-500 space-x-6">
                <span>{workflow.steps} steps</span>
                {workflow.lastRun && (
                  <span>Last run: {new Date(workflow.lastRun).toLocaleString()}</span>
                )}
                {workflow.nextRun && (
                  <span>Next run: {new Date(workflow.nextRun).toLocaleString()}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Run History */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Recent Runs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {runHistory.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{run.workflow}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      run.status === 'success'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(run.startTime).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{run.duration}</td>
                  <td className="px-6 py-4 text-sm">
                    <button className="text-indigo-600 hover:text-indigo-700">View Logs</button>
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
