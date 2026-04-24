import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProjectList from './pages/ProjectList';
import DefineProject from './pages/DefineProject';
import ReviewSuggestions from './pages/ReviewSuggestions';
import DesignView from './pages/DesignView';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <h1 className="text-xl font-bold text-blue-700">QbD-DOE</h1>
            <div className="text-sm text-gray-500">Process Development Suite</div>
          </div>
        </nav>
        
        <main className="py-8">
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/define" element={<DefineProject />} />
            <Route path="/review" element={<ReviewSuggestions />} />
            <Route path="/design" element={<DesignView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
