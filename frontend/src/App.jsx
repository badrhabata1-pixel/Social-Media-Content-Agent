import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import { Send, Copy, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';
import './App.css';

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

function App() {
  // ── States ──────────────────────────────────────────────────────────────────
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('Facebook');
  const [tone, setTone] = useState('professional');
  const [result, setResult] = useState(null); // { caption, hashtags, visual }
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ── API Call ────────────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic or idea first.');
      return;
    }
    setLoading(true);
    setResult(null);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim(), platform, tone }),
      });
      const data = await response.json();
      setResult(parseResult(data.data));
    } catch {
      setError('Could not connect to the Agent server. Make sure the backend (app.py) is running on port 8000.');
    }

    setLoading(false);
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(`${result.caption}\n\n${result.hashtags}`);
      alert('Copied to clipboard!');
    }
  };

  // Hashtag chips processing
  const hashtagChips = result?.hashtags
    ? result.hashtags.split(/\s+/).filter(Boolean)
    : [];

  return (
    <div className="app-layout">
      {/* ── Sidebar (from previous step) ── */}
      <Sidebar />

      {/* ── Main Content ── */}
      <main className="main-content">
        
        {/* Header */}
        <div className="page-header">
          <div className="header-badge"><Sparkles size={16}/> Intelligent Agent · PEAS Model</div>
          <h1>My Content Dashboard</h1>
          <p>Give the agent your idea, and it will reason about your requirements and generate a ready-to-publish post.</p>
        </div>

        <div className="content-wrapper">
          
          {/* ── Left Side: Sensors (Input) ── */}
          <div className="input-section card">
            <h3 className="section-title">1. Sensor Inputs (Agent Perception)</h3>
            
            <div className="field">
              <label>What is your post about?</label>
              <textarea
                value={topic}
                onChange={e => { setTopic(e.target.value); setError(''); }}
                placeholder="e.g. Artificial Intelligence, productivity tips..."
                rows="4"
              />
            </div>

            <div className="options-grid">
              <div className="field">
                <label>Target Platform</label>
                <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                  <option value="Facebook">Facebook 📘</option>
                  <option value="Twitter">Twitter/X 🐦</option>
                  <option value="Instagram">Instagram 📸</option>
                </select>
              </div>

              <div className="field">
                <label>Writing Tone</label>
                <select value={tone} onChange={(e) => setTone(e.target.value)}>
                  <option value="professional">Professional 💼</option>
                  <option value="funny">Funny & Casual 😂</option>
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
                <><div className="spinner" /> Agent is reasoning...</>
              ) : (
                <>Generate Content <Send size={18} /></>
              )}
            </button>
          </div>

          {/* ── Right Side: Actuators (Output) ── */}
          <div className="output-section card">
            <h3 className="section-title">2. Agent Output (Actuator Actions)</h3>

            {!result && !loading && (
              <div className="empty-state">
                The agent's generated content will appear here.
              </div>
            )}

            {loading && (
              <div className="loading-state">
                <div className="spinner-large"></div>
                <p>Agent is analyzing the environment and generating content...</p>
              </div>
            )}

            {result && !loading && (
              <div className="result-content">
                {/* Visual Concept */}
                {result.visual && (
                  <div className="result-visual">
                    <span className="visual-badge">🎨 Suggested Visual</span>
                    <p>{result.visual}</p>
                  </div>
                )}

                {/* Caption */}
                <div className="result-caption">
                  <h4>📝 Generated Caption:</h4>
                  <p>{result.caption}</p>
                </div>

                {/* Hashtags */}
                {hashtagChips.length > 0 && (
                  <div className="result-hashtags">
                    {hashtagChips.map((tag, i) => (
                      <span key={i} className="hashtag-chip">{tag}</span>
                    ))}
                  </div>
                )}

                <div className="action-buttons">
                  <button className="btn-outline" onClick={handleCopy}>
                    <Copy size={16} /> Copy Text
                  </button>
                  <button className="btn-outline" onClick={handleGenerate}>
                    <RefreshCw size={16} /> Regenerate
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Bottom: PEAS Summary Bar ── */}
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

      </main>
    </div>
  );
}

export default App;
