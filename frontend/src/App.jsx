import { useState } from 'react'
import './App.css'

// ── Platform & Tone Config ────────────────────────────────────────────────────
const PLATFORMS = [
  { value: 'Facebook',  label: 'Facebook',  icon: '📘' },
  { value: 'Twitter',   label: 'Twitter/X', icon: '🐦' },
  { value: 'Instagram', label: 'Instagram', icon: '📸' },
]

const TONES = [
  { value: 'professional', label: 'Professional', icon: '💼' },
  { value: 'funny',        label: 'Funny & Casual', icon: '😂' },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
function parseResult(raw) {
  // Split the backend text into structured sections
  const captionMatch  = raw.match(/📝 Caption:\s*([\s\S]*?)(?=#️⃣|🎨|$)/);
  const hashtagsMatch = raw.match(/#️⃣ Hashtags:\s*([\s\S]*?)(?=🎨|$)/);
  const visualMatch   = raw.match(/🎨 Visual Concept:\s*([\s\S]*)/);

  return {
    caption:  captionMatch  ? captionMatch[1].trim()  : raw.trim(),
    hashtags: hashtagsMatch ? hashtagsMatch[1].trim() : '',
    visual:   visualMatch   ? visualMatch[1].trim()   : '',
  }
}

// ── Component ─────────────────────────────────────────────────────────────────
function App() {
  const [topic,    setTopic]    = useState('')
  const [platform, setPlatform] = useState('Facebook')
  const [tone,     setTone]     = useState('professional')
  const [result,   setResult]   = useState(null)   // { caption, hashtags, visual }
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('⚠️  Please enter a topic or idea first.')
      return
    }
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/generate', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ topic: topic.trim(), platform, tone }),
      })
      const data = await response.json()
      setResult(parseResult(data.data))
    } catch {
      setError('❌  Could not connect to the Agent server. Make sure the backend (app.py) is running on port 8000.')
    }

    setLoading(false)
  }

  // Hashtag chips
  const hashtagChips = result?.hashtags
    ? result.hashtags.split(/\s+/).filter(Boolean)
    : []

  return (
    <div className="app-wrapper">

      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-badge">🤖 Intelligent Agent · PEAS Model</div>
        <h1>Social Media Content Agent</h1>
        <p>
          Give the agent your idea, target platform, and tone — it will reason
          about your requirements and generate a ready-to-publish post.
        </p>
      </header>

      {/* ── Sensors Card ── */}
      <div className="card">
        <div className="card-title">⚡ Sensor Inputs — Agent Perception</div>

        <div className="field-group">

          {/* Topic */}
          <div className="field">
            <label>📌 Topic / Idea</label>
            <input
              type="text"
              value={topic}
              onChange={e => { setTopic(e.target.value); setError('') }}
              placeholder="e.g. Artificial Intelligence, productivity tips, healthy eating…"
              onKeyDown={e => e.key === 'Enter' && handleGenerate()}
            />
          </div>

          {/* Platform */}
          <div className="field">
            <label>📱 Target Platform</label>
            <div className="platform-grid">
              {PLATFORMS.map(p => (
                <button
                  key={p.value}
                  className={`platform-btn${platform === p.value ? ' active' : ''}`}
                  onClick={() => setPlatform(p.value)}
                >
                  <span className="platform-icon">{p.icon}</span>
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tone */}
          <div className="field">
            <label>🎭 Writing Tone</label>
            <div className="tone-grid">
              {TONES.map(t => (
                <button
                  key={t.value}
                  className={`tone-btn${tone === t.value ? ' active' : ''}`}
                  onClick={() => setTone(t.value)}
                >
                  <span className="tone-icon">{t.icon}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Generate */}
        <button className="btn-generate" onClick={handleGenerate} disabled={loading}>
          {loading
            ? <><div className="spinner" /> Agent is reasoning…</>
            : <>✨ Generate Post</>}
        </button>
      </div>

      {/* ── Error ── */}
      {error && <div className="error-card">{error}</div>}

      {/* ── Actuator Output ── */}
      {result && (
        <div className="result-card">
          <div className="result-header">
            <div className="result-dot" />
            <h3>🎯 Agent Output — Actuator Actions</h3>
          </div>

          {/* Caption */}
          <div className="result-section">
            <div className="result-section-title">📝 Caption</div>
            <p>{result.caption}</p>
          </div>

          {/* Hashtags */}
          {hashtagChips.length > 0 && (
            <div className="result-section">
              <div className="result-section-title">#️⃣ Hashtags</div>
              <div className="hashtags-wrap">
                {hashtagChips.map((tag, i) => (
                  <span key={i} className="hashtag-chip">{tag}</span>
                ))}
              </div>
            </div>
          )}

          {/* Visual Concept */}
          {result.visual && (
            <div className="result-section">
              <div className="result-section-title">🎨 Visual Concept</div>
              <p>{result.visual}</p>
            </div>
          )}
        </div>
      )}

      {/* ── PEAS Summary Bar ── */}
      <div className="peas-bar">
        <div className="peas-item">
          <span className="peas-label">Performance</span>
          <span className="peas-value">Content quality & relevance</span>
        </div>
        <div className="peas-item">
          <span className="peas-label">Environment</span>
          <span className="peas-value">User + Social platforms</span>
        </div>
        <div className="peas-item">
          <span className="peas-label">Actuators</span>
          <span className="peas-value">Post · Hashtags · Visual</span>
        </div>
        <div className="peas-item">
          <span className="peas-label">Sensors</span>
          <span className="peas-value">Topic · Platform · Tone</span>
        </div>
      </div>

    </div>
  )
}

export default App