import { useState, useRef } from 'react'

// ── Mock subscription data (mirrors sandbox/mock_enterprise.py) ───────────────
const MOCK_SUBSCRIPTIONS = [
  {
    subscription_id:                'sw_101',
    vendor_name:                    'Notion',
    monthly_cost_usd:               120,
    seat_count:                     5,
    active_human_logins_last_90d:   0,
    is_headless_service_account:    false,
    has_webhook_dependency:         false,
    auto_renewal_date:              new Date(Date.now() + 45 * 86400000).toISOString().split('T')[0],
    cancellation_notice_window_days: 30,
    early_termination_fee_usd:      0,
    months_remaining:               2,
    status:                         null,
  },
  {
    subscription_id:                'sw_204',
    vendor_name:                    'Datadog',
    monthly_cost_usd:               340,
    seat_count:                     1,
    active_human_logins_last_90d:   0,
    is_headless_service_account:    true,   // ← TRAP A
    has_webhook_dependency:         true,
    auto_renewal_date:              new Date(Date.now() + 60 * 86400000).toISOString().split('T')[0],
    cancellation_notice_window_days: 0,
    early_termination_fee_usd:      0,
    months_remaining:               5,
    status:                         null,
  },
  {
    subscription_id:                'sw_307',
    vendor_name:                    'Figma',
    monthly_cost_usd:               200,
    seat_count:                     10,
    active_human_logins_last_90d:   0,
    is_headless_service_account:    false,
    has_webhook_dependency:         false,
    auto_renewal_date:              new Date(Date.now() + 25 * 86400000).toISOString().split('T')[0],
    cancellation_notice_window_days: 30,
    early_termination_fee_usd:      1800,  // ← TRAP B
    months_remaining:               9,
    status:                         null,
  },
  {
    subscription_id:                'sw_412',
    vendor_name:                    'Miro',
    monthly_cost_usd:               180,
    seat_count:                     20,
    active_human_logins_last_90d:   7,
    is_headless_service_account:    false,
    has_webhook_dependency:         false,
    auto_renewal_date:              new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0],
    cancellation_notice_window_days: 30,
    early_termination_fee_usd:      0,
    months_remaining:               6,
    status:                         null,
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
const ACTION_STYLES = {
  IMMEDIATE_CANCEL: { bg: 'bg-red-900/40',    border: 'border-red-500',    text: 'text-red-400',    label: '🗑 Cancel Now' },
  DOWNGRADE_TIER:   { bg: 'bg-amber-900/40',  border: 'border-amber-500',  text: 'text-amber-400',  label: '⬇ Downgrade' },
  SCHEDULE_NOTICE:  { bg: 'bg-blue-900/40',   border: 'border-blue-500',   text: 'text-blue-400',   label: '📅 Schedule Notice' },
  RENEGOTIATE:      { bg: 'bg-purple-900/40', border: 'border-purple-500', text: 'text-purple-400', label: '🤝 Renegotiate' },
  PROTECT:          { bg: 'bg-green-900/40',  border: 'border-green-500',  text: 'text-green-400',  label: '🛡 Protected' },
  PENDING:          { bg: 'bg-gray-800/40',   border: 'border-gray-600',   text: 'text-gray-400',   label: '⏳ Pending' },
}

function Badge({ action }) {
  const s = ACTION_STYLES[action] || ACTION_STYLES.PENDING
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${s.bg} ${s.border} ${s.text}`}>
      {s.label}
    </span>
  )
}

function SimulationStep({ step }) {
  const isWarning = step.includes('⚠️') || step.includes('🚨')
  const isOk      = step.includes('✅')
  return (
    <div className={`text-xs font-mono px-2 py-0.5 rounded ${
      isWarning ? 'text-red-300 bg-red-900/20' :
      isOk      ? 'text-green-300 bg-green-900/20' :
                  'text-gray-400'
    }`}>
      {step}
    </div>
  )
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function SubZeroDashboard() {
  const [subs, setSubs]               = useState(MOCK_SUBSCRIPTIONS)
  const [loading, setLoading]         = useState({})
  const [results, setResults]         = useState({})
  const [simLogs, setSimLogs]         = useState({})
  const [legalNotice, setLegalNotice] = useState(null)
  const [voiceLog, setVoiceLog]       = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const mediaRef                      = useRef(null)

  const totalMonthlyWaste = subs
    .filter(s => s.active_human_logins_last_90d === 0 && !s.is_headless_service_account)
    .reduce((sum, s) => sum + s.monthly_cost_usd, 0)

  // ── Run Full Audit for One Subscription ────────────────────────────────────
  async function runAudit(sub) {
    setLoading(prev => ({ ...prev, [sub.subscription_id]: true }))
    try {
      // Step 1: Decision Engine
      const decisionRes = await fetch('/api/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscription_id:                sub.subscription_id,
          vendor_name:                    sub.vendor_name,
          monthly_cost_usd:               sub.monthly_cost_usd,
          seat_count:                     sub.seat_count,
          active_human_logins_last_90d:   sub.active_human_logins_last_90d,
          has_webhook_dependency:         sub.has_webhook_dependency,
          is_headless_service_account:    sub.is_headless_service_account,
          auto_renewal_date:              sub.auto_renewal_date,
          cancellation_notice_window_days: sub.cancellation_notice_window_days,
          early_termination_fee_usd:      sub.early_termination_fee_usd,
          months_remaining:               sub.months_remaining,
        }),
      })
      const decision = await decisionRes.json()

      // Step 2: Digital Twin Simulation
      const simRes = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscription_id: sub.subscription_id,
          vendor_name:     sub.vendor_name,
          action:          decision.action,
        }),
      })
      const sim = await simRes.json()

      setResults(prev  => ({ ...prev, [sub.subscription_id]: decision }))
      setSimLogs(prev  => ({ ...prev, [sub.subscription_id]: sim }))
      setSubs(prev     => prev.map(s =>
        s.subscription_id === sub.subscription_id
          ? { ...s, status: decision.action }
          : s
      ))
    } catch (err) {
      console.error('Audit failed:', err)
    } finally {
      setLoading(prev => ({ ...prev, [sub.subscription_id]: false }))
    }
  }

  // ── Run All Audits ──────────────────────────────────────────────────────────
  async function runAllAudits() {
    for (const sub of subs) {
      await runAudit(sub)
    }
  }

  // ── Generate Legal Notice ───────────────────────────────────────────────────
  async function generateNotice(sub) {
    const res = await fetch('/api/generate-notice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vendor_name:            sub.vendor_name,
        contract_id:            sub.subscription_id,
        cancellation_clause:    'Section 9.1: Either party may terminate with 30 days written notice.',
        effective_date:         sub.auto_renewal_date,
        company_name:           'Acme Corp',
        signatory_name:         'Raj Patil',
        signatory_title:        'Chief Technology Officer',
      }),
    })
    const notice = await res.json()
    setLegalNotice(notice)
  }

  // ── Voice Recording ─────────────────────────────────────────────────────────
  async function toggleRecording() {
    if (isRecording) {
      mediaRef.current?.stop()
      setIsRecording(false)
      return
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    const chunks = []
    recorder.ondataavailable = e => chunks.push(e.data)
    recorder.onstop = async () => {
      const blob = new Blob(chunks, { type: 'audio/webm' })
      const form = new FormData()
      form.append('audio', blob, 'command.webm')
      const res  = await fetch('/api/voice-approve', { method: 'POST', body: form })
      const data = await res.json()
      setVoiceLog(data)
    }
    recorder.start()
    mediaRef.current = recorder
    setIsRecording(true)
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight">
            ❄️ <span className="text-cyan-400">SubZero</span> VeriDeprovision
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Verifiable Autonomous SaaS Deprovisioning &amp; Contract Renegotiation Engine
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={toggleRecording}
            className={`px-4 py-2 rounded-lg font-bold text-sm transition-all ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {isRecording ? '⏹ Stop Voice Command' : '🎙 Voice Approve'}
          </button>
          <button
            onClick={runAllAudits}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-bold text-sm transition-all"
          >
            🔍 Run Full Audit
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Monthly Waste Detected</p>
          <p className="text-3xl font-black text-red-400">${totalMonthlyWaste.toLocaleString()}</p>
          <p className="text-gray-500 text-xs mt-1">in zombie / idle SaaS seats</p>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Traps Detected</p>
          <p className="text-3xl font-black text-amber-400">
            {subs.filter(s => s.is_headless_service_account || s.early_termination_fee_usd > 0).length}
          </p>
          <p className="text-gray-500 text-xs mt-1">headless bots + contract penalties</p>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Actions Verified</p>
          <p className="text-3xl font-black text-green-400">
            {Object.keys(results).length} / {subs.length}
          </p>
          <p className="text-gray-500 text-xs mt-1">with Digital Twin proof</p>
        </div>
      </div>

      {/* Subscription Cards */}
      <div className="space-y-4">
        {subs.map(sub => {
          const result = results[sub.subscription_id]
          const sim    = simLogs[sub.subscription_id]
          const style  = ACTION_STYLES[sub.status || 'PENDING']

          return (
            <div
              key={sub.subscription_id}
              className={`border rounded-xl p-5 transition-all ${style.bg} ${style.border}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-bold text-lg">{sub.vendor_name}</h3>
                    <Badge action={sub.status || 'PENDING'} />
                    {sub.is_headless_service_account && (
                      <span className="px-2 py-0.5 rounded-full text-xs bg-red-950 border border-red-700 text-red-300 font-bold">
                        🤖 HEADLESS BOT TRAP
                      </span>
                    )}
                    {sub.early_termination_fee_usd > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-xs bg-amber-950 border border-amber-700 text-amber-300 font-bold">
                        💰 ETF ${sub.early_termination_fee_usd.toLocaleString()} TRAP
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 text-xs mt-1 font-mono">{sub.subscription_id}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => runAudit(sub)}
                    disabled={loading[sub.subscription_id]}
                    className="px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 disabled:opacity-50 rounded-lg text-xs font-bold transition-all"
                  >
                    {loading[sub.subscription_id] ? '⏳ Auditing...' : '▶ Audit'}
                  </button>
                  {result && result.action !== 'PROTECT' && (
                    <button
                      onClick={() => generateNotice(sub)}
                      className="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 rounded-lg text-xs font-bold transition-all"
                    >
                      📄 Notice
                    </button>
                  )}
                </div>
              </div>

              {/* Metadata Row */}
              <div className="grid grid-cols-5 gap-3 mb-3">
                {[
                  ['Monthly Cost', `$${sub.monthly_cost_usd}/mo`],
                  ['Seats', sub.seat_count],
                  ['Active Logins (90d)', sub.active_human_logins_last_90d],
                  ['ETF', sub.early_termination_fee_usd > 0 ? `$${sub.early_termination_fee_usd.toLocaleString()}` : 'None'],
                  ['Renewal', sub.auto_renewal_date],
                ].map(([label, value]) => (
                  <div key={label} className="bg-gray-900/60 rounded-lg p-2">
                    <p className="text-gray-500 text-xs">{label}</p>
                    <p className="text-white text-sm font-bold">{value}</p>
                  </div>
                ))}
              </div>

              {/* Decision Result */}
              {result && (
                <div className="bg-gray-900/80 rounded-lg p-3 mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-cyan-400">🧠 Muse Spark Reasoning</span>
                    <span className="text-xs text-gray-500">NPV: ${result.net_savings_usd?.toFixed(2)}</span>
                    {result.notice_deadline && (
                      <span className="text-xs text-amber-400">📅 Notice by: {result.notice_deadline}</span>
                    )}
                  </div>
                  {result.alert_message && (
                    <div className="text-xs text-amber-300 bg-amber-950/50 rounded p-2 mb-2">
                      {result.alert_message}
                    </div>
                  )}
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                    {result.reasoning_trace}
                  </pre>
                </div>
              )}

              {/* Simulation Logs */}
              {sim && (
                <div className="bg-gray-900/80 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-purple-400">🔬 Digital Twin Simulation</span>
                    <span className={`text-xs font-bold ${sim.status === 'SAFE' ? 'text-green-400' : 'text-red-400'}`}>
                      {sim.status === 'SAFE' ? '✅ SAFE' : '🚫 FAULT'}
                    </span>
                    {sim.safety_proof_hash && (
                      <span className="text-xs text-gray-500 font-mono">
                        proof: {sim.safety_proof_hash.slice(0, 16)}...
                      </span>
                    )}
                  </div>
                  <div className="space-y-0.5">
                    {sim.steps_executed?.map((step, i) => (
                      <SimulationStep key={i} step={step} />
                    ))}
                  </div>
                  {sim.fault_reason && (
                    <div className="mt-2 text-xs text-red-300 bg-red-950/50 rounded p-2">
                      {sim.fault_reason}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Voice Log Panel */}
      {voiceLog && (
        <div className="fixed bottom-6 right-6 w-96 bg-gray-900 border border-cyan-700 rounded-xl p-4 shadow-2xl">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-bold text-cyan-400">🎙 Voice Authorization</span>
            <button onClick={() => setVoiceLog(null)} className="text-gray-500 hover:text-white text-xs">✕</button>
          </div>
          <p className="text-xs text-gray-400 mb-1">Transcription:</p>
          <p className="text-sm text-white italic mb-2">"{voiceLog.transcription}"</p>
          <p className="text-xs text-gray-400">Approved: <span className="text-green-400">{voiceLog.approved_subscriptions?.join(', ') || 'None'}</span></p>
          <p className="text-xs text-gray-400">Denied: <span className="text-red-400">{voiceLog.denied_subscriptions?.join(', ') || 'None'}</span></p>
          <p className="text-xs text-gray-400">Global Approval: <span className={voiceLog.global_approval ? 'text-green-400' : 'text-red-400'}>{voiceLog.global_approval ? 'Yes' : 'No'}</span></p>
        </div>
      )}

      {/* Legal Notice Modal */}
      {legalNotice && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-purple-700 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg text-purple-400">📄 Legal Termination Notice</h3>
              <button onClick={() => setLegalNotice(null)} className="text-gray-500 hover:text-white">✕</button>
            </div>
            <pre className="text-sm text-gray-200 whitespace-pre-wrap font-mono leading-relaxed">
              {legalNotice.letter_body}
            </pre>
            <div className="mt-4 pt-4 border-t border-gray-700 flex gap-2 justify-end">
              <button
                onClick={() => navigator.clipboard.writeText(legalNotice.letter_body)}
                className="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 rounded-lg text-xs font-bold"
              >
                📋 Copy Letter
              </button>
              <button
                onClick={() => setLegalNotice(null)}
                className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-xs font-bold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
