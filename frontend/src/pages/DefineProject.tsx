import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const DefineProject: React.FC = () => {
  const navigate = useNavigate();
  const [apiName, setApiName] = useState('');
  const [chemistry, setChemistry] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('current_project');
    if (saved) {
      const p = JSON.parse(saved);
      setApiName(p.api_name || '');
      setChemistry(p.chemistry_description || '');
    }
  }, []);

  const getSuggestions = async () => {
    if (!apiName || !chemistry) {
      alert('Please fill in both fields');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_name: apiName, chemistry_description: chemistry }),
      });
      const data = await res.json();
      localStorage.setItem('suggestions', JSON.stringify(data));
      navigate('/review');
    } catch (e) {
      alert('Suggestion failed. Proceeding with manual entry.');
      navigate('/review');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Define Project</h1>
      
      <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">API Name</label>
          <input
            type="text"
            value={apiName}
            onChange={e => setApiName(e.target.value)}
            placeholder="e.g., Finerenone intermediate"
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Chemistry / Process Description</label>
          <textarea
            value={chemistry}
            onChange={e => setChemistry(e.target.value)}
            placeholder="Describe the reaction: reagents, catalysts, solvents, conditions..."
            rows={6}
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="flex gap-4">
          <button
            onClick={getSuggestions}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : '🔍 Get AI Suggestions'}
          </button>
          <button
            onClick={() => navigate('/review')}
            className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300"
          >
            Skip Suggestions →
          </button>
        </div>
      </div>
    </div>
  );
};

export default DefineProject;
