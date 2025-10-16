// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TercerosPage from './pages/Terceros';
import Contabilidad from './pages/Contabilidad';
import Facturacion from './pages/Facturacion';
import { authService } from './services/auth';

// Componente para rutas protegidas
const ProtectedRoute = ({ children }) => {
  const isAuth = authService.isAuthenticated();
  return isAuth ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="terceros" element={<TercerosPage />} />
          <Route path="contabilidad" element={<Contabilidad />} />
          <Route path="facturacion" element={<Facturacion />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;