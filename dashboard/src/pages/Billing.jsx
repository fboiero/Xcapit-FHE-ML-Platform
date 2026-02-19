import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: 'forever',
    description: 'For individuals and small projects',
    features: [
      '10 API requests/minute',
      '100 requests/day',
      '2 ML models',
      '1 consortium',
      'Community support',
    ],
    limits: { rate: 10, daily: 100, models: 2, consortiums: 1 },
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 49,
    period: 'month',
    description: 'For small teams getting started',
    features: [
      '100 API requests/minute',
      '5,000 requests/day',
      '10 ML models',
      '5 consortiums',
      'Email support',
      'Basic analytics',
    ],
    limits: { rate: 100, daily: 5000, models: 10, consortiums: 5 },
    popular: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 199,
    period: 'month',
    description: 'For growing businesses',
    features: [
      '500 API requests/minute',
      '50,000 requests/day',
      '50 ML models',
      '20 consortiums',
      'Priority support',
      'Advanced analytics',
      'Webhooks',
      'Custom integrations',
    ],
    limits: { rate: 500, daily: 50000, models: 50, consortiums: 20 },
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    period: 'custom',
    description: 'For large organizations',
    features: [
      'Unlimited API requests',
      'Unlimited daily requests',
      'Unlimited ML models',
      'Unlimited consortiums',
      '24/7 dedicated support',
      'SLA guarantees',
      'Custom deployment',
      'On-premise option',
      'Advanced security',
    ],
    limits: { rate: -1, daily: -1, models: -1, consortiums: -1 },
  },
]

const invoices = [
  { id: 'INV-001', date: '2024-01-01', amount: 199, status: 'paid', description: 'Professional Plan - January 2024' },
  { id: 'INV-002', date: '2023-12-01', amount: 199, status: 'paid', description: 'Professional Plan - December 2023' },
  { id: 'INV-003', date: '2023-11-01', amount: 199, status: 'paid', description: 'Professional Plan - November 2023' },
  { id: 'INV-004', date: '2023-10-01', amount: 49, status: 'paid', description: 'Starter Plan - October 2023' },
]

export default function Billing() {
  const { t } = useTranslation()
  const [currentPlan, setCurrentPlan] = useState('professional')
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [billingCycle, setBillingCycle] = useState('monthly')

  // Simulated usage data
  const usage = {
    apiRequests: { used: 32450, limit: 50000 },
    models: { used: 12, limit: 50 },
    consortiums: { used: 8, limit: 20 },
    storage: { used: 2.4, limit: 10 }, // GB
  }

  const currentPlanData = plans.find(p => p.id === currentPlan)

  const getUsagePercentage = (used, limit) => {
    if (limit === -1) return 0
    return Math.min(100, (used / limit) * 100)
  }

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const handleUpgrade = (planId) => {
    setSelectedPlan(plans.find(p => p.id === planId))
    setShowUpgradeModal(true)
  }

  const confirmUpgrade = () => {
    setCurrentPlan(selectedPlan.id)
    setShowUpgradeModal(false)
    setSelectedPlan(null)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Billing & Subscription</h1>
        <p className="text-gray-600">Manage your subscription and view usage</p>
      </div>

      {/* Current Plan */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-indigo-100 text-sm">Current Plan</p>
            <h2 className="text-3xl font-bold">{currentPlanData?.name}</h2>
            <p className="text-indigo-100 mt-1">{currentPlanData?.description}</p>
          </div>
          <div className="text-right">
            {currentPlanData?.price !== null ? (
              <>
                <div className="text-4xl font-bold">${currentPlanData?.price}</div>
                <div className="text-indigo-100">per month</div>
              </>
            ) : (
              <div className="text-2xl font-bold">Custom pricing</div>
            )}
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-white/20 flex items-center justify-between">
          <div className="text-sm text-indigo-100">
            Next billing date: February 1, 2024
          </div>
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="px-4 py-2 bg-white text-indigo-600 rounded-lg font-medium hover:bg-indigo-50"
          >
            Change Plan
          </button>
        </div>
      </div>

      {/* Usage */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Current Usage</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* API Requests */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">API Requests (Today)</span>
              <span className="font-medium">
                {usage.apiRequests.used.toLocaleString()} / {usage.apiRequests.limit.toLocaleString()}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(getUsagePercentage(usage.apiRequests.used, usage.apiRequests.limit))}`}
                style={{ width: `${getUsagePercentage(usage.apiRequests.used, usage.apiRequests.limit)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {Math.round(getUsagePercentage(usage.apiRequests.used, usage.apiRequests.limit))}% used
            </p>
          </div>

          {/* Models */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">ML Models</span>
              <span className="font-medium">{usage.models.used} / {usage.models.limit}</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(getUsagePercentage(usage.models.used, usage.models.limit))}`}
                style={{ width: `${getUsagePercentage(usage.models.used, usage.models.limit)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {Math.round(getUsagePercentage(usage.models.used, usage.models.limit))}% used
            </p>
          </div>

          {/* Consortiums */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Consortiums</span>
              <span className="font-medium">{usage.consortiums.used} / {usage.consortiums.limit}</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(getUsagePercentage(usage.consortiums.used, usage.consortiums.limit))}`}
                style={{ width: `${getUsagePercentage(usage.consortiums.used, usage.consortiums.limit)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {Math.round(getUsagePercentage(usage.consortiums.used, usage.consortiums.limit))}% used
            </p>
          </div>

          {/* Storage */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Storage</span>
              <span className="font-medium">{usage.storage.used} GB / {usage.storage.limit} GB</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(getUsagePercentage(usage.storage.used, usage.storage.limit))}`}
                style={{ width: `${getUsagePercentage(usage.storage.used, usage.storage.limit)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {Math.round(getUsagePercentage(usage.storage.used, usage.storage.limit))}% used
            </p>
          </div>
        </div>
      </div>

      {/* Plans Comparison */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Available Plans</h3>
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                billingCycle === 'monthly' ? 'bg-white shadow text-gray-900' : 'text-gray-600'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                billingCycle === 'yearly' ? 'bg-white shadow text-gray-900' : 'text-gray-600'
              }`}
            >
              Yearly (Save 20%)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map(plan => {
            const isCurrentPlan = plan.id === currentPlan
            const yearlyPrice = plan.price ? Math.round(plan.price * 0.8 * 12) : null
            const displayPrice = billingCycle === 'yearly' && plan.price ? Math.round(plan.price * 0.8) : plan.price

            return (
              <div
                key={plan.id}
                className={`relative rounded-xl border-2 p-6 ${
                  plan.popular ? 'border-indigo-500' : isCurrentPlan ? 'border-green-500' : 'border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-indigo-500 text-white text-xs font-medium rounded-full">
                    Most Popular
                  </div>
                )}
                {isCurrentPlan && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full">
                    Current Plan
                  </div>
                )}

                <h4 className="text-xl font-bold text-gray-900">{plan.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{plan.description}</p>

                <div className="mt-4">
                  {displayPrice !== null ? (
                    <>
                      <span className="text-3xl font-bold">${displayPrice}</span>
                      <span className="text-gray-500">/month</span>
                      {billingCycle === 'yearly' && plan.price && (
                        <p className="text-sm text-gray-500 mt-1">
                          ${yearlyPrice} billed yearly
                        </p>
                      )}
                    </>
                  ) : (
                    <span className="text-xl font-bold">Contact us</span>
                  )}
                </div>

                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => !isCurrentPlan && handleUpgrade(plan.id)}
                  disabled={isCurrentPlan}
                  className={`w-full mt-6 px-4 py-2 rounded-lg font-medium transition-colors ${
                    isCurrentPlan
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : plan.popular
                        ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {isCurrentPlan ? 'Current Plan' : plan.price === null ? 'Contact Sales' : 'Upgrade'}
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Payment Method */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Payment Method</h3>
        <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
          <div className="flex items-center gap-4">
            <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white text-xs font-bold">
              VISA
            </div>
            <div>
              <div className="font-medium">Visa ending in 4242</div>
              <div className="text-sm text-gray-500">Expires 12/2025</div>
            </div>
          </div>
          <button className="text-indigo-600 hover:text-indigo-800 font-medium">
            Update
          </button>
        </div>
      </div>

      {/* Invoice History */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Invoice History</h3>
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 text-sm font-medium text-gray-500">Invoice</th>
              <th className="text-left py-3 text-sm font-medium text-gray-500">Date</th>
              <th className="text-left py-3 text-sm font-medium text-gray-500">Description</th>
              <th className="text-left py-3 text-sm font-medium text-gray-500">Amount</th>
              <th className="text-left py-3 text-sm font-medium text-gray-500">Status</th>
              <th className="text-right py-3 text-sm font-medium text-gray-500">Download</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(invoice => (
              <tr key={invoice.id} className="border-b border-gray-100">
                <td className="py-3 font-medium">{invoice.id}</td>
                <td className="py-3 text-gray-600">{new Date(invoice.date).toLocaleDateString()}</td>
                <td className="py-3 text-gray-600">{invoice.description}</td>
                <td className="py-3 font-medium">${invoice.amount}</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium capitalize">
                    {invoice.status}
                  </span>
                </td>
                <td className="py-3 text-right">
                  <button className="text-indigo-600 hover:text-indigo-800">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">
              {selectedPlan ? `Upgrade to ${selectedPlan.name}` : 'Change Plan'}
            </h3>

            {!selectedPlan ? (
              <div className="space-y-3">
                {plans.filter(p => p.id !== currentPlan).map(plan => (
                  <button
                    key={plan.id}
                    onClick={() => setSelectedPlan(plan)}
                    className="w-full p-4 border border-gray-200 rounded-lg hover:border-indigo-500 text-left"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">{plan.name}</div>
                        <div className="text-sm text-gray-500">{plan.description}</div>
                      </div>
                      {plan.price !== null ? (
                        <div className="font-bold">${plan.price}/mo</div>
                      ) : (
                        <div className="text-sm text-gray-500">Contact us</div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="flex justify-between mb-2">
                    <span>New plan</span>
                    <span className="font-medium">{selectedPlan.name}</span>
                  </div>
                  <div className="flex justify-between mb-2">
                    <span>Price</span>
                    <span className="font-medium">
                      {selectedPlan.price !== null ? `$${selectedPlan.price}/mo` : 'Custom'}
                    </span>
                  </div>
                  <div className="flex justify-between border-t pt-2 mt-2">
                    <span className="font-medium">Due today</span>
                    <span className="font-bold">
                      {selectedPlan.price !== null ? `$${selectedPlan.price}` : '-'}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mb-4">
                  Your new plan will take effect immediately. You'll be charged the prorated amount for the remaining days in your billing cycle.
                </p>
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowUpgradeModal(false)
                  setSelectedPlan(null)
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              {selectedPlan && selectedPlan.price !== null && (
                <button
                  onClick={confirmUpgrade}
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Confirm Upgrade
                </button>
              )}
              {selectedPlan && selectedPlan.price === null && (
                <button className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                  Contact Sales
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
