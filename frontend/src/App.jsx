import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CreateAssignment from './pages/CreateAssignment';
import AssignmentDetail from './pages/AssignmentDetail';
import Results from './pages/Results';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<CreateAssignment />} />
          <Route path="/assignment/:id" element={<AssignmentDetail />} />
          <Route path="/results/:id" element={<Results />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;

