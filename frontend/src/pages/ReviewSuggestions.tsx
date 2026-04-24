import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ReviewSuggestions: React.FC = () => {
  const navigate = useNavigate();
  const [cqas, setCqas] = useState<any[]>([]);
  const [cpps, setCpps] = useState<any[]>([]);
  const [reviewed, setReviewed] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('suggestions');
    if (saved) {
      const data = JSON.parse(saved);
      setCqas(data.suggested_CQAs || []);
      setCpps(data.suggested_CPPs || []);
    } else {
      // Demo defaults
      setCqas([
        { name: 'Assay', unit: '%', target: 98, lower_spec: 95, upper_spec: 102, weight: 5, goal: 'target', rationale: 'Critical quality attribute', confidence: 'high' },
        { name: 'Total_Impurities', unit: '%', target: 0.5, lower_spec: 0, upper_spec: 2.0, weight: 5, goal: 'minimize', rationale: 'Patient safety', confidence: 'high' },
        { name: 'Yield', unit: '%', target: 85, lower_spec: 70, upper_spec: 100, weight: 3, goal: 'maximize', rationale: 'Economic viability', confidence: 'high' },
      ]);
      setCpps([
        { name: 'Temperature', unit: '°C', type: 'continuous', low: 70, center: 80, high: 90, rationale: 'Reaction kinetics', confidence: 'medium', safety_flag: false },
        { name: 'Catalyst_Loading', unit: 'mol%', type: 'continuous', low: 1, center: 3, high: 5, rationale: 'Rate control', confidence: 'medium', safety_flag: false },
        { name: 'Time', unit: 'h', type: 'continuous', low: 2, center: 4, high: 6, rationale: 'Conversion', confidence: 'medium', safety_flag: false },
        { name: 'Base_eq', unit: 'eq', type: 'continuous', low: 1.5, center: 2.0, high: 2.5, rationale: 'Stoichiometry', confidence: 'medium', safety_flag: false },
        { name: 'Solvent_Ratio', unit: 'ratio', type: 'continuous', low: 3, center: 5, high: 7, rationale: 'Solubility', confidence: 'medium', safety_flag: false },
      ]);
    }
  }, []);

  const generateDesign = () => {
    if (!reviewed) {
      alert('Please confirm you have reviewed all flagged items');
      return;
    }
    // Save to localStorage
    localStorage.setItem('project_cqas', JSON.stringify(cqas));
    localStorage.setItem('project_cpps', JSON.stringify(cpps));
    navigate('/design');
  };

  const confidenceColor = (c: string) => {
    if (c === 'high') return 'bg-green-100 text-green-700';
    if (c === 'medium') return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <p className="text-yellow-800 font-medium">
          ⚠️ AI suggestions are starting points. Bad ranges = bad DOE. Verify against your process knowledge.
        </p>
      </div>

      <h1 className="text-2xl font-bold mb-6">Review Suggestions</h1>

      {/* CQAs */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Critical Quality Attributes (CQAs)</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Unit</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Target</th>
                <th className="px-4 py-3 text-left text-sm font-medium">LSL</th>
                <th className="px-4 py-3 text-left text-sm font-medium">USL</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Weight</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Goal</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {cqas.map((cqa, i) => (
                <tr key={i} className="border-t">
                  <td className="px-4 py-3">{cqa.name}</td>
                  <td className="px-4 py-3">{cqa.unit}</td>
                  <td className="px-4 py-3">{cqa.target}</td>
                  <td className="px-4 py-3">{cqa.lower_spec}</td>
                  <td className="px-4 py-3">{cqa.upper_spec}</td>
                  <td className="px-4 py-3">{cqa.weight}</td>
                  <td className="px-4 py-3">{cqa.goal}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${confidenceColor(cqa.confidence)}`}>
                      {cqa.confidence}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CPPs */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Critical Process Parameters (CPPs)</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Unit</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Low</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Center</th>
                <th className="px-4 py-3 text-left text-sm font-medium">High</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Confidence</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Safety</th>
              </tr>
            </thead>
            <tbody>
              {cpps.map((cpp, i) => (
                <tr key={i} className={`border-t ${cpp.safety_flag ? 'bg-red-50' : ''}`}>
                  <td className="px-4 py-3">{cpp.name}</td>
                  <td className="px-4 py-3">{cpp.unit}</td>
                  <td className="px-4 py-3">{cpp.low}</td>
                  <td className="px-4 py-3">{cpp.center}</td>
                  <td className="px-4 py-3">{cpp.high}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${confidenceColor(cpp.confidence)}`}>
                      {cpp.confidence}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {cpp.safety_flag && <span className="text-red-600" title="Safety flag">⚠️</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Gate */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={reviewed}
            onChange={e => setReviewed(e.target.checked)}
            className="w-5 h-5 text-blue-600"
          />
          <span className="font-medium">
            I have reviewed all flagged items as a qualified process chemist
          </span>
        </label>
      </div>

      <div className="flex gap-4">
        <button
          onClick={generateDesign}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
        >
          Generate Design →
        </button>
      </div>
    </div>
  );
};

export default ReviewSuggestions;
