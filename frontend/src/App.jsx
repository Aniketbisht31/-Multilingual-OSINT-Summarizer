import { 
  Shield, 
  Activity, 
  Globe, 
  Search, 
  Plus, 
  Clock, 
  MapPin, 
  AlertTriangle,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import api, { getBriefs, ingestManual } from './api/client';

const App = () => {
  const [briefs, setBriefs] = useState([]);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestUrl, setIngestUrl] = useState('');
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [selectedBrief, setSelectedBrief] = useState(null);
  const scrollRef = useRef(null);

  // Fetch initial briefs
  const fetchBriefs = async () => {
    try {
      const resp = await getBriefs();
      setBriefs(resp.data);
    } catch (err) {
      console.error('Failed to fetch briefs', err);
    }
  };

  useEffect(() => {
    fetchBriefs();
    
    // Setup WebSocket
    const setupWebSocket = () => {
      const socket = new WebSocket(`ws://${window.location.host}/ws/feed`);
      
      socket.onopen = () => setWsStatus('connected');
      socket.onclose = () => {
        setWsStatus('disconnected');
        setTimeout(setupWebSocket, 3000); // Reconnect
      };
      
      socket.onmessage = (event) => {
        const newBrief = JSON.parse(event.data);
        setBriefs(prev => [newBrief, ...prev]);
      };
      
      return socket;
    };

    const ws = setupWebSocket();
    return () => ws.close();
  }, []);

  const handleManualIngest = async (e) => {
    e.preventDefault();
    if (!ingestUrl) return;
    setIsIngesting(true);
    try {
      await ingestManual({ 
        url: ingestUrl, 
        language: 'hi' // Default to Hindi for manual test
      });
      setIngestUrl('');
      // Ingress status reported via WS
    } catch (err) {
      alert('Ingestion failed');
    } finally {
      setIsIngesting(false);
    }
  };

  const getUrgencyClass = (urgency) => {
    switch(urgency?.toUpperCase()) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      default: return 'badge-border';
    }
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <Shield size={28} color="#8b5cf6" />
          <span>OSINT DRDO</span>
        </div>

        <nav style={{ marginTop: '1rem' }}>
          <div className="nav-item active">
            <Activity size={20} />
            <span>Live Feed</span>
          </div>
          <div className="nav-item">
            <Globe size={20} />
            <span>Regional Map</span>
          </div>
          <div className="nav-item">
            <Search size={20} />
            <span>Archive</span>
          </div>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <div className={`nav-item ${wsStatus === 'connected' ? 'active' : ''}`} style={{ cursor: 'default' }}>
            <div style={{ 
              width: 8, height: 8, borderRadius: '50%', 
              background: wsStatus === 'connected' ? '#10b981' : '#f43f5e',
              boxShadow: wsStatus === 'connected' ? '0 0 8px #10b981' : 'none'
            }} />
            <span>Pipeline: {wsStatus}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <h1 className="title">Threat Monitoring</h1>
          <form onSubmit={handleManualIngest} style={{ display: 'flex', gap: '0.75rem' }}>
            <input 
              className="glass"
              type="url" 
              placeholder="Paste URL to analyze..."
              value={ingestUrl}
              onChange={(e) => setIngestUrl(e.target.value)}
              style={{ padding: '0.625rem 1rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--card-border)', color: 'white', borderRadius: '10px', width: '300px' }}
            />
            <button 
              className="glass"
              disabled={isIngesting}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1.25rem', color: 'white', fontWeight: '500', cursor: 'pointer' }}
            >
              <Plus size={18} />
              {isIngesting ? 'Processing...' : 'Ingest'}
            </button>
          </form>
        </header>

        <section className="feed" ref={scrollRef}>
          {briefs.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-dim)' }}>
              <RefreshCw className="animate-spin" size={32} style={{ marginBottom: '1rem' }} />
              <p>Scanning intelligence sources...</p>
            </div>
          ) : (
            briefs.map((item, idx) => {
              const b = item.brief || item; // Handle both direct and wrapper formats
              return (
                <div key={item.id || idx} className="glass brief-card" onClick={() => setSelectedBrief(item)}>
                  <div className="card-header">
                    <div>
                      <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>{b.threat_assessment?.category || 'General Signal'}</h3>
                      <div className="badge badge-border" style={{ fontSize: '0.65rem' }}>
                        {b.source?.original_language?.toUpperCase() || 'HI'} → EN
                      </div>
                    </div>
                    <span className={`badge ${getUrgencyClass(b.threat_assessment?.urgency)}`}>
                      {b.threat_assessment?.urgency || 'LOW'}
                    </span>
                  </div>

                  <p className="brief-summary">{b.summary}</p>

                  <div className="card-footer">
                    <div className="meta-group">
                      <div className="meta-item">
                        <Clock size={14} />
                        <span>{new Date(b.source?.published_at || item.created_at).toLocaleTimeString()}</span>
                      </div>
                      <div className="meta-item">
                        <MapPin size={14} />
                        <span>{b.key_entities?.[0]?.name || 'Regional'}</span>
                      </div>
                    </div>
                    <ChevronRight size={18} opacity={0.5} />
                  </div>
                </div>
              );
            })
          )}
        </section>
      </main>

      {/* Detail Modal Overlay */}
      {selectedBrief && (
        <div 
          onClick={() => setSelectedBrief(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}
        >
          <div 
            onClick={e => e.stopPropagation()}
            className="glass" 
            style={{ maxWidth: '800px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2.5rem', background: '#121214' }}
          >
            <div style={{ marginBottom: '2rem' }}>
              <div className={`badge ${getUrgencyClass(selectedBrief.brief?.threat_assessment?.urgency)}`} style={{ marginBottom: '1rem' }}>
                {selectedBrief.brief?.threat_assessment?.urgency} PRIORITY
              </div>
              <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{selectedBrief.brief?.threat_assessment?.category}</h2>
              <p style={{ color: 'var(--text-dim)' }}>Analysis generated at {new Date(selectedBrief.created_at).toLocaleString()}</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2.5rem' }}>
              <div className="glass" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem', fontSize: '0.875rem', textTransform: 'uppercase' }}>Analyst Summary</h4>
                <p style={{ lineHeight: '1.6' }}>{selectedBrief.brief?.summary}</p>
              </div>
              <div className="glass" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem', fontSize: '0.875rem', textTransform: 'uppercase' }}>Source Details</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                   <p><strong>Trust Score:</strong> {selectedBrief.brief?.source?.credibility_score}/5</p>
                   <p><strong>Rationale:</strong> {selectedBrief.brief?.source?.credibility_rationale}</p>
                   <p><strong>Sentiment:</strong> {selectedBrief.brief?.threat_assessment?.sentiment}</p>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <h4 style={{ marginBottom: '1rem' }}>Key Entities Identified</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                {selectedBrief.brief?.key_entities?.map((ent, i) => (
                  <div key={i} className="glass" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
                    <span style={{ color: 'var(--text-dim)', marginRight: '0.5rem' }}>{ent.type}</span>
                    {ent.name}
                  </div>
                ))}
              </div>
            </div>

            <div className="glass" style={{ padding: '1.5rem', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>
                <AlertTriangle size={20} />
                <h4 style={{ fontSize: '0.875rem', textTransform: 'uppercase' }}>Recommended Action</h4>
              </div>
              <p style={{ fontWeight: '600' }}>{selectedBrief.brief?.recommended_action}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
