import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import { Send, Copy, RefreshCw, AlertCircle, Sparkles, Check } from 'lucide-react';
import './App.css';

// ── Directive Config Options ────────────────────────────────────────────────
const PLATFORMS = [
  { value: 'LinkedIn',  label: 'LinkedIn',  icon: '💼' },
  { value: 'Instagram', label: 'Instagram', icon: '📸' },
  { value: 'Twitter',   label: 'Twitter / X', icon: '🐦' },
  { value: 'Facebook',  label: 'Facebook',  icon: '📘' },
];

const GOALS = [
  { value: 'Marketing',   label: 'Marketing (AIDA)',            icon: '🚀' },
  { value: 'Educational', label: 'Educational (PAS)',           icon: '💡' },
  { value: 'Engagement',  label: 'Engagement (Story-Lesson)',   icon: '💬' },
];

const TONES = [
  { value: 'Professional',  label: 'Professional',  icon: '💼' },
  { value: 'Inspirational', label: 'Inspirational', icon: '✨' },
  { value: 'Casual',         label: 'Casual',        icon: '☕' },
];

const LANGUAGES = [
  { value: 'en', label: 'English', icon: '🇬🇧' },
  { value: 'ar', label: 'العربية (Arabic)', icon: '🇸🇦' },
];

function App() {
  // ── Sensor Directives States ──────────────────────────────────────────────
  const [topic, setTopic] = useState('Time management mobile application for college students');
  const [keywords, setKeywords] = useState('tasks, productivity, study routine');
  const [platform, setPlatform] = useState('LinkedIn');
  const [goal, setGoal] = useState('Marketing');
  const [tone, setTone] = useState('Professional');
  const [language, setLanguage] = useState('en');

  // ── Output States ─────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState(0); // 0 = Option A, 1 = Option B
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic or concept first.');
      return;
    }

    setLoading(true);
    setResult(null);
    setError('');
    setCopied(false);

    const kwList = keywords
      .split(',')
      .map(k => k.trim())
      .filter(Boolean);

    try {
      const response = await fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(),
          keywords: kwList,
          platform,
          goal,
          tone,
          language,
        }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setResult(data.data);
        setActiveTab(0);
      } else {
        setError('Agent returned an unexpected error response.');
      }
    } catch {
      setError('Could not connect to backend server. Ensure app.py is running on port 8000.');
    }

    setLoading(false);
  };

  const handleCopy = (text) => {
    if (text) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const currentVariation = result?.variations?.[activeTab];

  return (
    <div className={`app-layout ${language === 'ar' ? 'lang-arabic' : ''}`}>
      {/* ── Sidebar Component from GitHub Theme ── */}
      <Sidebar />

      {/* ── Main Content Area ── */}
      <main className="main-content">
        
        {/* Header */}
        <div className="page-header">
          <div className="header-badge">
            <Sparkles size={16} /> Module 3 · AI Content Writer Agent (Offline NLG)
          </div>
          <h1>My Content Dashboard</h1>
          <p>
            Transforms high-level directives into platform-compliant, multi-angle publications using deterministic PEAS reasoning.
          </p>
        </div>

        <div className="content-wrapper">
          
          {/* ── Left Side: Sensor Directives (Inputs) ── */}
          <div className="input-section card">
            <h3 className="section-title">1. Sensor Inputs (Agent Perception)</h3>
            
            {/* Topic */}
            <div className="field">
              <label>📌 What is your post idea / topic?</label>
              <textarea
                value={topic}
                onChange={e => { setTopic(e.target.value); setError(''); }}
                placeholder="e.g. Time management mobile application for college students..."
                rows="3"
              />
            </div>

            {/* Keywords */}
            <div className="field">
              <label>🏷️ Keywords (Comma-separated)</label>
              <input
                type="text"
                value={keywords}
                onChange={e => setKeywords(e.target.value)}
                placeholder="tasks, productivity, study routine"
              />
            </div>

            {/* Language & Platform Grid */}
            <div className="options-grid">
              <div className="field">
                <label>🌐 Target Language</label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                  {LANGUAGES.map(l => (
                    <option key={l.value} value={l.value}>{l.icon} {l.label}</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>📱 Target Platform</label>
                <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                  {PLATFORMS.map(p => (
                    <option key={p.value} value={p.value}>{p.icon} {p.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Goal & Tone Grid */}
            <div className="options-grid">
              <div className="field">
                <label>🎯 Campaign Goal & Framework</label>
                <select value={goal} onChange={(e) => setGoal(e.target.value)}>
                  {GOALS.map(g => (
                    <option key={g.value} value={g.value}>{g.icon} {g.label}</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>🎭 Tone of Voice</label>
                <select value={tone} onChange={(e) => setTone(e.target.value)}>
                  {TONES.map(t => (
                    <option key={t.value} value={t.value}>{t.icon} {t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <button className="generate-btn" onClick={handleGenerate} disabled={loading}>
              {loading ? (
                <><div className="spinner" /> Agent is reasoning offline...</>
              ) : (
                <>Synthesize Content <Send size={18} /></>
              )}
            </button>
          </div>

          {/* ── Right Side: Actuator Outputs ── */}
          <div className="output-section card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className="section-title">2. Agent Output (Actuator Actions)</h3>
              {result && (
                <span style={{ fontSize: '0.8rem', color: '#9090b8', fontWeight: 600 }}>
                  {result.agent_metadata.framework} · {result.agent_metadata.platform}
                </span>
              )}
            </div>

            {!result && !loading && (
              <div className="empty-state">
                The agent's multi-variation generated content will appear here.
              </div>
            )}

            {loading && (
              <div className="loading-state">
                <div className="spinner-large"></div>
                <p>Agent is selecting copywriting frameworks and synthesizing copy offline...</p>
              </div>
            )}

            {result && !loading && currentVariation && (
              <div className="result-content" dir={result.agent_metadata.language === 'ar' ? 'rtl' : 'ltr'}>
                
                {/* Variation Tabs */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }} dir="ltr">
                  {result.variations.map((v, idx) => (
                    <button
                      key={v.version_id}
                      type="button"
                      className={`btn-outline ${activeTab === idx ? 'active' : ''}`}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        fontSize: '0.85rem',
                        background: activeTab === idx ? 'var(--primary, #6c63ff)' : 'transparent',
                        color: activeTab === idx ? '#fff' : 'inherit',
                        border: '1px solid var(--border, rgba(108, 99, 255, 0.25))',
                        borderRadius: '8px',
                        cursor: 'pointer'
                      }}
                      onClick={() => setActiveTab(idx)}
                    >
                      {idx === 0 ? '⚡ Option A: ' : '🌱 Option B: '} {v.type}
                    </button>
                  ))}
                </div>

                {/* Hook */}
                <div className="result-caption" style={{ marginBottom: '14px' }}>
                  <h4>🪝 Attention Hook:</h4>
                  <p style={{ fontWeight: 600 }}>{currentVariation.hook}</p>
                </div>

                {/* Body */}
                <div className="result-caption" style={{ marginBottom: '14px' }}>
                  <h4>📖 Content Body:</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{currentVariation.body}</p>
                </div>

                {/* Call to Action */}
                <div className="result-caption" style={{ marginBottom: '14px' }}>
                  <h4>🎯 Call to Action (CTA):</h4>
                  <p>{currentVariation.call_to_action}</p>
                </div>

                {/* Hashtags */}
                {currentVariation.hashtags?.length > 0 && (
                  <div className="result-hashtags">
                    {currentVariation.hashtags.map((tag, i) => (
                      <span key={i} className="hashtag-chip">{tag}</span>
                    ))}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="action-buttons" dir="ltr">
                  <button className="btn-outline" onClick={() => handleCopy(currentVariation.full_caption)}>
                    {copied ? <Check size={16} color="#43e97b" /> : <Copy size={16} />}
                    {copied ? 'Copied Full Post!' : 'Copy Ready-to-Publish Caption'}
                  </button>
                  <button className="btn-outline" onClick={handleGenerate}>
                    <RefreshCw size={16} /> Regenerate
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Bottom: PEAS Formalization Summary Bar ── */}
        <div className="peas-bar">
          <div className="peas-item">
            <span className="peas-label">Performance</span>
            <span className="peas-value">AIDA / PAS Structural Adherence</span>
          </div>
          <div className="peas-item">
            <span className="peas-label">Environment</span>
            <span className="peas-value">LinkedIn · Instagram · X · Facebook</span>
          </div>
          <div className="peas-item">
            <span className="peas-label">Actuators</span>
            <span className="peas-value">Hooks · Body · CTAs · Hashtags</span>
          </div>
          <div className="peas-item">
            <span className="peas-label">Sensors</span>
            <span className="peas-value">Directive Schema (JSON)</span>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
