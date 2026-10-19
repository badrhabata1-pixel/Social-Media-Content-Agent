import { Suspense, lazy, useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import ImagePanel from './components/ImagePanel';
import {
  Send, Copy, RefreshCw, AlertCircle, Sparkles, Check, PenLine, ChartColumn, CircleCheck, ExternalLink, X,
} from 'lucide-react';
import { API_BASE, BACKEND_UNREACHABLE, apiErrorMessage, readJson } from './api';
import './App.css';

// Loaded on first visit to the Analytics tab, so the charting library stays out of the initial bundle.
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'));
const SUCCESS_TOAST_MS = 10000;

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
  const [submittedDirective, setSubmittedDirective] = useState(null);
  const [generationId, setGenerationId] = useState(0);
  const [view, setView] = useState('create'); // 'create' | 'analytics'

  // ── Publishing States ─────────────────────────────────────────────────────
  const [generatedImage, setGeneratedImage] = useState(null); // file name reported by ImagePanel
  const [publishing, setPublishing] = useState(false);
  const [published, setPublished] = useState({});              // variation index -> Facebook URL
  const [toast, setToast] = useState(null);                    // { type, title, message, url? }

  useEffect(() => {
    if (toast?.type !== 'success') return undefined;
    const timer = setTimeout(() => setToast(null), SUCCESS_TOAST_MS);
    return () => clearTimeout(timer);
  }, [toast]);

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

    const directive = { topic: topic.trim(), keywords: kwList, platform, goal, tone, language };

    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(directive),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setResult(data.data);
        setActiveTab(0);
        setSubmittedDirective(directive);
        setGenerationId(id => id + 1);
        setGeneratedImage(null); // a new post starts without an image
        setPublished({});
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

  const handlePublishFacebook = async () => {
    if (!currentVariation || publishing) return;
    const asPhoto = Boolean(generatedImage);
    const confirmed = window.confirm(
      `Publish this ${asPhoto ? 'photo post' : 'post'} publicly to your Facebook Page?`,
    );
    if (!confirmed) return;

    const variationIndex = activeTab; // the user may switch tabs while the request runs
    setPublishing(true);
    setToast(null);
    try {
      const response = await fetch(`${API_BASE}/publish/facebook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentVariation.full_caption,
          topic: submittedDirective?.topic ?? null,
          domain: result.agent_metadata.detected_domain ?? null,
          tone: result.agent_metadata.tone ?? null,
          image_filename: generatedImage,
        }),
      });
      const payload = await readJson(response);
      if (!response.ok || payload?.status !== 'success') {
        throw new Error(apiErrorMessage(payload, response.status));
      }
      setPublished(prev => ({ ...prev, [variationIndex]: payload.data.url }));
      setToast({
        type: 'success',
        title: 'Published to Facebook',
        message: asPhoto ? 'Your photo post is live on the Page.' : 'Your post is live on the Page.',
        url: payload.data.url,
      });
    } catch (err) {
      setToast({
        type: 'error',
        title: 'Publishing failed',
        message: err instanceof TypeError ? BACKEND_UNREACHABLE : err.message,
      });
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className={`app-layout ${language === 'ar' ? 'lang-arabic' : ''}`}>
      {/* ── Sidebar Component from GitHub Theme ── */}
      <Sidebar activeView={view} onNavigate={setView} />

      {/* ── Main Content Area ── */}
      <main className="main-content">
        
        {/* Header */}
        <div className="page-header">
          <div className="header-badge">
            <Sparkles size={16} /> Module 3 · AI Content Writer Agent (Offline NLG)
          </div>
          <h1>My Content Dashboard</h1>
          <p>
            Transforms high-level directives into platform-compliant, multi-angle publications using rule-based PEAS reasoning.
          </p>
        </div>

        {/* ── View tabs: the Create view stays mounted (hidden) so a generated post survives a tab switch ── */}
        <div className="view-tabs" role="tablist" aria-label="Dashboard views">
          <button type="button" role="tab" aria-selected={view === 'create'}
                  className={view === 'create' ? 'active' : ''} onClick={() => setView('create')}>
            <PenLine size={16} /> Create Post
          </button>
          <button type="button" role="tab" aria-selected={view === 'analytics'}
                  className={view === 'analytics' ? 'active' : ''} onClick={() => setView('analytics')}>
            <ChartColumn size={16} /> Analytics Dashboard
          </button>
        </div>

        {view === 'analytics' && (
          <Suspense fallback={<div className="loading-state card"><div className="spinner-large" /></div>}>
            <AnalyticsDashboard />
          </Suspense>
        )}

        <div className="content-wrapper" hidden={view !== 'create'}>
          
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

                {/* Publish: a photo post when ImagePanel has produced an image, otherwise a text post */}
                <div className="publish-row" dir="ltr">
                  {published[activeTab] ? (
                    <a className="btn-facebook" href={published[activeTab]} target="_blank" rel="noreferrer">
                      <Check size={18} /> Published · View on Facebook <ExternalLink size={16} />
                    </a>
                  ) : (
                    <button className="btn-facebook" onClick={handlePublishFacebook} disabled={publishing}>
                      {publishing ? (
                        <><div className="spinner" /> Publishing…</>
                      ) : (
                        <><Send size={18} /> {generatedImage ? 'Publish Photo Post to Facebook' : 'Publish to Facebook'}</>
                      )}
                    </button>
                  )}
                </div>

                <ImagePanel
                  key={generationId}
                  directive={submittedDirective}
                  hook={currentVariation.hook}
                  onImageReady={setGeneratedImage}
                />
              </div>
            )}
          </div>
        </div>

        {/* ── Bottom: PEAS Formalization Summary Bar ── */}
        <div className="peas-bar" hidden={view !== 'create'}>
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

      {/* ── Publish result toast ── */}
      {toast && (
        <div className={`toast toast-${toast.type}`} role={toast.type === 'error' ? 'alert' : 'status'}>
          {toast.type === 'success' ? <CircleCheck size={20} /> : <AlertCircle size={20} />}
          <div className="toast-body">
            <strong>{toast.title}</strong>
            <span>{toast.message}</span>
            {toast.url && (
              <a href={toast.url} target="_blank" rel="noreferrer">
                {toast.url} <ExternalLink size={14} />
              </a>
            )}
          </div>
          <button type="button" className="toast-close" onClick={() => setToast(null)} aria-label="Dismiss">
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
