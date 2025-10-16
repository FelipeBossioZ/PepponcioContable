// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { 
  Users, 
  FileText, 
  TrendingUp, 
  DollarSign,
  ArrowUp,
  ArrowDown,
  Activity,
  ShoppingCart
} from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({
    terceros: 0,
    facturas: 0,
    ventas: 0,
    asientos: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Llamar a tus endpoints para obtener estadísticas
      const [terceros, facturas] = await Promise.all([
        axios.get('http://localhost:8000/api/terceros/terceros/'),
        axios.get('http://localhost:8000/api/facturacion/facturas/')
      ]);
      
      setStats({
        terceros: terceros.data.length,
        facturas: facturas.data.length,
        ventas: facturas.data.reduce((sum, f) => sum + parseFloat(f.total || 0), 0),
        asientos: 0 // Implementar endpoint de conteo
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const cards = [
    { 
      title: 'Total Terceros', 
      value: stats.terceros, 
      icon: Users, 
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      change: '+12%',
      changeType: 'increase'
    },
    { 
      title: 'Facturas Emitidas', 
      value: stats.facturas, 
      icon: FileText, 
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
      change: '+8%',
      changeType: 'increase'
    },
    { 
      title: 'Ventas Totales', 
      value: `$${stats.ventas.toLocaleString('es-CO')}`, 
      icon: DollarSign, 
      color: 'bg-yellow-500',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600',
      change: '+23%',
      changeType: 'increase'
    },
    { 
      title: 'Asientos Contables', 
      value: stats.asientos, 
      icon: TrendingUp, 
      color: 'bg-purple-500',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      change: '-5%',
      changeType: 'decrease'
    },
  ];

  const recentActivity = [
    { id: 1, type: 'factura', description: 'Nueva factura #1234 creada', time: 'Hace 2 horas' },
    { id: 2, type: 'tercero', description: 'Cliente ABC Corp. agregado', time: 'Hace 3 horas' },
    { id: 3, type: 'asiento', description: 'Asiento contable registrado', time: 'Hace 5 horas' },
    { id: 4, type: 'factura', description: 'Factura #1233 pagada', time: 'Hace 1 día' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Resumen general del sistema contable</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cards.map((card, index) => (
          <div key={index} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-6 w-6 ${card.textColor}`} />
              </div>
              <span className={`text-sm font-medium flex items-center ${
                card.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
              }`}>
                {card.changeType === 'increase' ? (
                  <ArrowUp className="h-4 w-4 mr-1" />
                ) : (
                  <ArrowDown className="h-4 w-4 mr-1" />
                )}
                {card.change}
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{card.value}</h3>
            <p className="text-sm text-gray-600 mt-1">{card.title}</p>
          </div>
        ))}
      </div>

      {/* Contenido adicional */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Actividad Reciente */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Actividad Reciente</h2>
            <Activity className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 py-3 border-b border-gray-100 last:border-0">
                <div className="flex-shrink-0 w-2 h-2 mt-2 bg-indigo-600 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Resumen de Ventas */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Resumen de Ventas</h2>
            <ShoppingCart className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Ventas del mes</span>
              <span className="text-lg font-semibold text-gray-900">$2,450,000</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Facturas pendientes</span>
              <span className="text-lg font-semibold text-yellow-600">12</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Clientes activos</span>
              <span className="text-lg font-semibold text-green-600">45</span>
            </div>
            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-900">Total recaudado</span>
                <span className="text-xl font-bold text-indigo-600">$8,750,000</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;