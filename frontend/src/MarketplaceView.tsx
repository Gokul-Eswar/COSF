import React, { useState, useEffect } from 'react';
import { Search, Package, CheckCircle, Download, ExternalLink, Loader2, ArrowLeft } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  type: 'playbook' | 'adapter';
  verified: boolean;
  author: string;
  created_at: string;
}

interface MarketplaceViewProps {
  onBack: () => void;
  onInstalled: (draftId: string) => void;
}

const MarketplaceView: React.FC<MarketplaceViewProps> = ({ onBack, onInstalled }) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch(`${API_BASE}/marketplace/templates`);
        const data = await response.json();
        setTemplates(data);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  const handleInstall = async (id: string) => {
    setInstalling(id);
    try {
      const response = await fetch(`${API_BASE}/marketplace/templates/${id}/install`, {
        method: 'POST'
      });
      const data = await response.json();
      if (response.ok) {
        alert('Successfully installed!');
        if (data.draft_id) {
          onInstalled(data.draft_id);
        }
      } else {
        alert(`Failed to install: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Install error:', error);
      alert('Error connecting to API.');
    } finally {
      setInstalling(null);
    }
  };

  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(search.toLowerCase()) || 
    t.description.toLowerCase().includes(search.toLowerCase()) ||
    t.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="marketplace-container">
      <header className="app-header">
        <div className="logo-section">
          <button className="back-button" onClick={onBack}>
            <ArrowLeft size={18} />
          </button>
          <div className="logo">COSF Marketplace</div>
        </div>
        <div className="search-box">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search playbooks and adapters..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </header>

      <div className="marketplace-content">
        {loading ? (
          <div className="loading-state">
            <Loader2 className="animate-spin" size={48} />
            <p>Loading community templates...</p>
          </div>
        ) : (
          <div className="template-grid">
            {filteredTemplates.map(template => (
              <div key={template.id} className="template-card">
                <div className="card-header">
                  <div className="template-type">
                    <Package size={14} />
                    <span>{template.type}</span>
                  </div>
                  {template.verified && (
                    <div className="verified-badge" title="Verified by COSF Team">
                      <CheckCircle size={14} fill="currentColor" className="check-icon" />
                    </div>
                  )}
                </div>
                <h3>{template.name}</h3>
                <p>{template.description}</p>
                <div className="tags">
                  {template.tags.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
                <div className="card-footer">
                  <span className="author">by {template.author}</span>
                  <button 
                    className="install-btn"
                    disabled={installing === template.id}
                    onClick={() => handleInstall(template.id)}
                  >
                    {installing === template.id ? <Loader2 className="animate-spin" size={16} /> : <Download size={16} />}
                    Install
                  </button>
                </div>
              </div>
            ))}
            {filteredTemplates.length === 0 && (
              <div className="empty-state">
                <p>No templates found matching your search.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketplaceView;
