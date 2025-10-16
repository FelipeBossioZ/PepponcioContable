import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
// CRUCIAL: Asegúrate de que esta línea esté, es la que carga Tailwind
import './index.css'; 

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);