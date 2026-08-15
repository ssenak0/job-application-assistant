import { useState, useRef } from 'react';
import './App.css';

function App() {
  const [jobDescription, setJobDescription] = useState('');
  const [generateCoverLetter, setGenerateCoverLetter] = useState(false);
  const [generateRecruiterMessage, setGenerateRecruiterMessage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  // File Upload State
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    if (selectedFile.type !== 'application/pdf') {
      setError('Lütfen sadece PDF formatında CV yükleyin.');
      return;
    }
    
    setFile(selectedFile);
    setUploadStatus('Yükleniyor...');
    
    // Yükleme İşlemi (API)
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload-cv', {
        method: 'POST',
        body: formData,
      });
      if (response.ok) {
        setUploadStatus('✅ CV Başarıyla Analiz Edildi!');
      } else {
        throw new Error('Yükleme başarısız.');
      }
    } catch (err) {
      setUploadStatus('❌ Yükleme hatası.');
      setError(err.message);
    }
  };

  const handleGenerate = async () => {
    if (!jobDescription.trim()) {
      setError('Lütfen bir iş ilanı metni giriniz.');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/tailor', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          description: jobDescription,
          generate_cover_letter: generateCoverLetter,
          generate_recruiter_message: generateRecruiterMessage
        }),
      });

      if (!response.ok) {
        throw new Error('Bir hata oluştu, CV üretilemedi.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>✨ AI Kariyer & CV Asistanı</h1>
        <p>Kendi CV'nizi yükleyin, ilan metnini yapıştırın, saniyeler içinde özel CV'niz hazır olsun.</p>
      </header>

      <main className="main-content">
        <div className="left-panel">
          <h2>📄 1. Profilinizi Yükleyin</h2>
          <div 
            className="upload-zone"
            onClick={() => fileInputRef.current.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              style={{display: 'none'}} 
              accept="application/pdf"
              onChange={handleFileChange}
            />
            <div className="upload-icon">☁️</div>
            <p>{file ? file.name : 'Mevcut CV\'nizi Sürükleyin veya Seçin (PDF)'}</p>
            {uploadStatus && <span className="upload-status">{uploadStatus}</span>}
          </div>

          <h2 style={{marginTop: '2rem'}}>📝 2. İlan Girdisi</h2>
          <div className="input-group">
            <textarea 
              placeholder="İlan gereksinimlerini ve sorumluluklarını buraya yapıştırın..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          <div className="options-group">
            <label className="checkbox-container">
              <input 
                type="checkbox" 
                checked={generateCoverLetter}
                onChange={(e) => setGenerateCoverLetter(e.target.checked)}
              />
              İlana Özel Ön Yazı (Cover Letter) Üret
            </label>
            <label className="checkbox-container" style={{marginLeft: '15px'}}>
              <input 
                type="checkbox" 
                checked={generateRecruiterMessage}
                onChange={(e) => setGenerateRecruiterMessage(e.target.checked)}
              />
              LinkedIn İK Mesajı Üret
            </label>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            className="generate-btn" 
            onClick={handleGenerate}
            disabled={isLoading}
          >
            {isLoading ? '⏳ Yapay Zeka Çalışıyor...' : '🚀 İlana Özel CV\'mi Üret'}
          </button>
        </div>

        <div className="right-panel">
          <h2>📊 Analiz ve Sonuç</h2>
          
          {!result && !isLoading && (
            <div className="empty-state">
              <span className="icon">📄</span>
              <p>Sonuçları ve üretilen CV'nizi burada göreceksiniz.</p>
            </div>
          )}

          {isLoading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Yapay zeka CV'nizi yeniden şekillendiriyor...</p>
            </div>
          )}

          {result && (
            <div className="result-container">
              <div className="score-card">
                <h3>Eşleşme Skoru: <span>{result.score}/100</span></h3>
                <div className="skills-analysis">
                  <div className="matched">
                    <strong>✅ Eşleşenler:</strong> {result.matched_skills.join(', ') || '-'}
                  </div>
                  <div className="missing">
                    <strong>⚠️ Eksikler:</strong> {result.missing_skills.join(', ') || '-'}
                  </div>
                </div>
              </div>

              <div className="pdf-preview">
                <iframe 
                  src={`http://127.0.0.1:8000${result.pdf_url}`} 
                  title="CV Preview" 
                  className="pdf-frame"
                ></iframe>
              </div>

              <div className="action-buttons">
                <a 
                  href={`http://127.0.0.1:8000${result.pdf_url}`} 
                  download 
                  className="download-btn"
                  target="_blank"
                  rel="noreferrer"
                >
                  📥 CV İndir (PDF)
                </a>
                
                {result.cover_letter_url && (
                  <a 
                    href={`http://127.0.0.1:8000${result.cover_letter_url}`} 
                    download 
                    className="download-btn cover-letter-btn"
                    target="_blank"
                    rel="noreferrer"
                  >
                    📝 Ön Yazıyı İndir (TXT)
                  </a>
                )}
              </div>
              
              {result.recruiter_message && (
                <div className="message-preview" style={{marginTop: '20px', padding: '15px', backgroundColor: '#f0f9ff', borderRadius: '8px', border: '1px solid #bae6fd'}}>
                  <h4 style={{marginTop: 0, color: '#0369a1', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <span>💬 LinkedIn İK Mesajı</span>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(result.recruiter_message);
                        alert("Mesaj kopyalandı!");
                      }}
                      style={{padding: '4px 10px', fontSize: '0.8rem', background: '#0ea5e9', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                    >
                      Kopyala
                    </button>
                  </h4>
                  <p style={{margin: '10px 0 0 0', fontSize: '0.95rem', color: '#334155', whiteSpace: 'pre-wrap'}}>
                    {result.recruiter_message}
                  </p>
                </div>
              )}
              
              {result.cover_letter_text && (
                <div className="message-preview" style={{marginTop: '20px', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #cbd5e1'}}>
                  <h4 style={{marginTop: 0, color: '#334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <span>📝 İlana Özel Ön Yazı (Cover Letter)</span>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(result.cover_letter_text);
                        alert("Ön yazı kopyalandı!");
                      }}
                      style={{padding: '4px 10px', fontSize: '0.8rem', background: '#64748b', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                    >
                      Kopyala
                    </button>
                  </h4>
                  <p style={{margin: '10px 0 0 0', fontSize: '0.95rem', color: '#475569', whiteSpace: 'pre-wrap'}}>
                    {result.cover_letter_text}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
