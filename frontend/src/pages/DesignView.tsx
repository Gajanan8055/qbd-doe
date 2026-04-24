import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const DesignView: React.FC = () => {
  const navigate = useNavigate();
  const [design, setDesign] = useState<any[]>([]);
  const [info, setInfo] = useState<any>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    generateDesign();
  }, []);

  const generateDesign = async () => {
    setLoading(true);
    const cpps = JSON.parse(localStorage.getItem('project_cpps') || '[]');
    
    try {
      const res = await fetch('/api/designs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: 'demo',
          design_type: 'CCD',
          factors: cpps,
        }),
      });
      const data = await res.json();
      setDesign(data.design || []);
      setInfo(data.info || {});
    } catch (e) {
      // Fallback: show demo design
      setDesign([
        { Run: 1, StdOrder: 1, RunOrder: 15, Block: 1, Temperature: 70, Catalyst_Loading: 1, Time: 2, Base_eq: 1.5, Solvent_Ratio: 3, Notes: '' },
        { Run: 2, StdOrder: 2, RunOrder: 8, Block: 1, Temperature: 90, Catalyst_Loading: 1, Time: 2, Base_eq: 1.5, Solvent_Ratio: 3, Notes: '' },
        { Run: 3, StdOrder: 3, RunOrder: 22, Block: 1, Temperature: 70, Catalyst_Loading: 5, Time: 2, Base_eq: 1.5, Solvent_Ratio: 3, Notes: '' },
      ]);
      setInfo({ type: 'CCD', n_factors: 5, n_total_runs: 32 });
    }
    setLoading(false);
  };

  const downloadCSV = () => {
    const headers = Object.keys(design[0] || {}).join(',');
    const rows = design.map(row => Object.values(row).join(',')).join('\n');
    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'CCD_design.csv';
    a.click();
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Experimental Design</h1>

      {/* Design Info Card */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{info.n_total_runs || 32}</div>
            <div className="text-sm text-gray-500">Total Runs</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{info.n_factors || 5}</div>
            <div className="text-sm text-gray-500">Factors</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{info.center_points || 6}</div>
            <div className="text-sm text-gray-500">Center Points</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{info.alpha?.toFixed(2) || '2.00'}</div>
            <div className="text-sm text-gray-500">Alpha</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={downloadCSV}
          className="bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700"
        >
          ⬇️ Download Experiment CSV
        </button>
        <button
          onClick={() => navigate('/upload')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
        >
          Upload Results →
        </button>
      </div>

      {/* Design Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                {design.length > 0 && Object.keys(design[0]).map(key => (
                  <th key={key} className="px-4 py-3 text-left text-sm font-medium">{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {design.slice(0, 20).map((row, i) => (
                <tr key={i} className="border-t hover:bg-gray-50">
                  {Object.values(row).map((val, j) => (
                    <td key={j} className="px-4 py-3 text-sm">{typeof val === 'number' ? val.toFixed(2) : val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {design.length > 20 && (
          <div className="p-4 text-center text-gray-500">
            ... {design.length - 20} more rows
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignView;
