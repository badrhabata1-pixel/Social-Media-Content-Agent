import { useEffect, useState } from 'react';
import { Check, Copy, Download, ImageIcon, RefreshCw, TriangleAlert, WandSparkles } from 'lucide-react';
import { API_BASE, imageFilename } from '../api';
import './ImagePanel.css';

function frameStyle(aspectRatio) {
  const [w, h] = aspectRatio.split(':').map(Number);
  return { aspectRatio: `${w} / ${h}`, '--frame-ratio': w / h };
}

// onImageReady(filename | null) tells the parent which generated image can be published with the post.
function ImagePanel({ directive, hook, onImageReady }) {
  const [engine, setEngine] = useState(null);
  const [visual, setVisual] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/image-service/status`)
      .then(res => res.json())
      .then(data => { if (!cancelled) setEngine(data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setCopied(false);
    try {
      const response = await fetch(`${API_BASE}/generate-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...directive, hook }),
      });
      const payload = await response.json();
      if (response.ok && payload.status === 'success') {
        setVisual(payload.data);
        onImageReady?.(imageFilename(payload.data.image_url));
      } else {
        setError('The server rejected the image request. Check the post inputs and try again.');
      }
    } catch {
      setError('Could not reach the image service. Ensure app.py is running on port 8000.');
    }
    setLoading(false);
  };

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(visual.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const aiReady = engine?.ai_generation_available;
  const direction = visual?.visual_direction;

  return (
    <section className="result-visual image-panel" dir="ltr">
      <div className="image-panel-header">
        <span className="visual-badge"><ImageIcon size={14} /> Post Visual</span>
        {engine && (
          <span className={`image-engine ${aiReady ? 'online' : 'offline'}`}>
            {aiReady ? `Nano Banana · ${engine.models[0]}` : 'Prompt-only mode'}
          </span>
        )}
      </div>

      {!visual && !loading && (
        <button className="btn-outline image-generate-btn" onClick={handleGenerate}>
          <WandSparkles size={16} />
          {engine && !aiReady ? 'Create Image Prompt & Design Brief' : 'Generate Post Image'}
        </button>
      )}

      {loading && !visual && (
        <div className="image-loading">
          <div className="spinner-large" />
          <p>Art-directing the visual and rendering it...</p>
        </div>
      )}

      {error && (
        <div className="error-message"><TriangleAlert size={16} /> {error}</div>
      )}

      {visual && (
        <>
          {visual.image_url ? (
            <figure
              className={`image-frame ${loading ? 'is-loading' : ''}`}
              style={frameStyle(direction.aspect_ratio)}
            >
              <img src={visual.image_url} alt={`Visual for the post: ${directive.topic}`} />
              {loading && <div className="image-frame-overlay"><div className="spinner-large" /></div>}
            </figure>
          ) : (
            <div className="image-notice">
              <TriangleAlert size={18} />
              <span>{visual.notice}</span>
            </div>
          )}

          <div className="image-meta">
            <span className="image-chip">{direction.aspect_ratio} · {direction.dimensions}px</span>
            <span className="image-chip">{direction.visual_style}</span>
            <span className="image-chip">{direction.framework}</span>
            {visual.model && <span className="image-chip">{visual.model}</span>}
            <span className="image-palette">
              {direction.palette.map(color => (
                <span
                  key={color.hex}
                  className="image-swatch"
                  style={{ background: color.hex }}
                  title={`${color.name} ${color.hex}`}
                />
              ))}
            </span>
          </div>

          <details className="image-details" open={!visual.image_url}>
            <summary>Image prompt & design brief</summary>
            <p className="image-prompt">{visual.prompt}</p>
            <dl className="image-brief">
              <dt>Composition</dt><dd>{direction.composition}</dd>
              <dt>Lighting</dt><dd>{direction.lighting}</dd>
              <dt>Text overlay</dt><dd>{direction.text_overlay}</dd>
              <dt>Platform</dt><dd>{direction.platform_notes}</dd>
            </dl>
          </details>

          <div className="action-buttons">
            {visual.image_url && (
              <a className="btn-outline" href={`${visual.image_url}?download=true`}>
                <Download size={16} /> Download
              </a>
            )}
            <button className="btn-outline" onClick={handleCopyPrompt}>
              {copied ? <Check size={16} color="#43e97b" /> : <Copy size={16} />}
              {copied ? 'Prompt Copied!' : 'Copy Prompt'}
            </button>
            <button className="btn-outline" onClick={handleGenerate} disabled={loading}>
              <RefreshCw size={16} /> {visual.image_url ? 'Regenerate Image' : 'Try Again'}
            </button>
          </div>
        </>
      )}
    </section>
  );
}

export default ImagePanel;
