import { useState } from 'react'
import './App.css'

function App() {
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('Facebook')
  const [tone, setTone] = useState('professional')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!topic) {
      alert("Please enter a topic!");
      return;
    }
    setLoading(true);
    setResult('');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic, platform: platform, tone: tone })
      });
      
      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      console.error("Error:", error);
      setResult("❌ Error: Cannot connect to Agent server.");
    }
    
    setLoading(false);
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: 'auto', textAlign: 'center', color: '#fff' }}>
      <h1>🤖 Rule-Based Content Agent</h1>
      <p>Give the agent inputs, and it will use its logic to create a post!</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', textAlign: 'left', backgroundColor: '#1a1a1a', padding: '20px', borderRadius: '10px' }}>
        
        {/* Sensor 1: الفكرة */}
        <label>📌 Topic / Idea:</label>
        <input 
          type="text" 
          value={topic} 
          onChange={(e) => setTopic(e.target.value)} 
          placeholder="مثال: الذكاء الاصطناعي، المذاكرة، البرمجة..."
          style={{ padding: '10px', borderRadius: '5px', fontSize: '16px' }}
        />

        {/* Sensor 2: المنصة */}
        <label>📱 Platform:</label>
        <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ padding: '10px', borderRadius: '5px', fontSize: '16px' }}>
          <option value="Facebook">Facebook</option>
          <option value="Twitter">Twitter</option>
          <option value="Instagram">Instagram</option>
        </select>

        {/* Sensor 3: أسلوب الكتابة */}
        <label>🎭 Tone / Style:</label>
        <select value={tone} onChange={(e) => setTone(e.target.value)} style={{ padding: '10px', borderRadius: '5px', fontSize: '16px' }}>
          <option value="professional">رسمي واحترافي (Professional)</option>
          <option value="funny">ساخر ومضحك (Funny)</option>
        </select>
      </div>

      <button 
        onClick={handleGenerate} 
        disabled={loading}
        style={{ marginTop: '20px', padding: '12px 25px', backgroundColor: '#646cff', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' }}
      >
        {loading ? 'Agent is thinking...' : 'Let Agent Create Post'}
      </button>

      {/* Actuator: المخرجات */}
      {result && (
        <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#2a2a2a', borderRadius: '10px', textAlign: 'left', borderLeft: '5px solid #646cff' }}>
          <h3 style={{ marginTop: 0, color: '#646cff' }}>Agent Output:</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', fontSize: '16px' }}>{result}</p>
        </div>
      )}
    </div>
  )
}

export default App