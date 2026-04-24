import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([
    { id: 'demo-suzuki-001', name: 'Suzuki coupling — Finerenone step 4', status: 'completed', date: '2026-04-24' },
  ]);

  const loadDemo = async () => {
    try {
      const res = await fetch('/api/demo');
      const data = await res.json();
      // Store demo data and navigate
      localStorage.setItem('current_project', JSON.stringify(data));
      navigate('/define');
    } catch (e) {
      alert('Failed to load demo');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-xl p-8 mb-8">
        <h1 className="text-3xl font-bold mb-2">QbD-DOE Process Development</h1>
        <p className="text-blue-100">Quality by Design — Design of Experiments for Pharmaceutical R&D</p>
        <div className="mt-6 flex gap-4">
          <button
            onClick={loadDemo}
            className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            🚀 Load Suzuki Demo
          </button>
          <button
            onClick={() => navigate('/define')}
            className="bg-blue-700 text-white border border-blue-500 px-6 py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
          >
            + New Project
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Projects</h2>
        {projects.length === 0 ? (
          <p className="text-gray-500">No projects yet. Start with the demo or create a new project.</p>
        ) : (
          <div className="space-y-3">
            {projects.map(p => (
              <div key={p.id} className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                   onClick={() => navigate('/design')}>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-lg">{p.name}</h3>
                    <p className="text-sm text-gray-500">{p.id} • {p.date}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    p.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {p.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-4 text-center">
          <div className="text-3xl mb-2">📊</div>
          <h3 className="font-semibold">Statistical Analysis</h3>
          <p className="text-sm text-gray-500">ANOVA, regression, diagnostics</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 text-center">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="font-semibold">Optimization</h3>
          <p className="text-sm text-gray-500">Desirability + Monte Carlo</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-4 text-center">
          <div className="text-3xl mb-2">📄</div>
          <h3 className="font-semibold">Word Reports</h3>
          <p className="text-sm text-gray-500">Professional QbD reports</p>
        </div>
      </div>
    </div>
  );
};

export default ProjectList;
