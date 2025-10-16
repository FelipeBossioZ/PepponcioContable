// frontend/src/pages/Terceros.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TercerosTabla from '../components/TercerosTabla';
import { Users, Plus, Search, Upload, X } from 'lucide-react';

const TercerosPage = () => {
    const [terceros, setTerceros] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busqueda, setBusqueda] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        tipo_documento: 'CC',
        numero_documento: '',
        nombre_razon_social: '',
        direccion: '',
        telefono: '',
        email: ''
    });

    useEffect(() => {
        fetchTerceros();
    }, []);

    const fetchTerceros = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/terceros/terceros/');
            setTerceros(response.data);
        } catch (err) {
            console.error("Error al cargar terceros:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post('http://localhost:8000/api/terceros/terceros/', formData);
            setShowModal(false);
            fetchTerceros(); // Recargar la lista
            setFormData({
                tipo_documento: 'CC',
                numero_documento: '',
                nombre_razon_social: '',
                direccion: '',
                telefono: '',
                email: ''
            });
        } catch (error) {
            alert('Error al crear el tercero');
        }
    };

    const handleImport = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv,.xlsx';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                alert('La función de importar desde Excel está en desarrollo. Por ahora usa el Admin de Django.');
            }
        };
        input.click();
    };

    // Filtrar terceros
    const tercerosFiltrados = terceros.filter(tercero => 
        tercero.nombre_razon_social.toLowerCase().includes(busqueda.toLowerCase()) ||
        tercero.numero_documento.includes(busqueda)
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }
    
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="mb-8">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Gestión de Terceros</h1>
                        <p className="mt-2 text-gray-600">Administra clientes, proveedores y otros terceros</p>
                    </div>
                    <div className="flex space-x-3">
                        <button 
                            onClick={handleImport}
                            className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 bg-white rounded-lg hover:bg-gray-50"
                        >
                            <Upload className="h-5 w-5 mr-2" />
                            Importar
                        </button>
                        <button 
                            onClick={() => setShowModal(true)}
                            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                        >
                            <Plus className="h-5 w-5 mr-2" />
                            Nuevo Tercero
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar por nombre, documento o email..."
                        className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        value={busqueda}
                        onChange={(e) => setBusqueda(e.target.value)}
                    />
                </div>
            </div>
            
            <TercerosTabla data={tercerosFiltrados} onRefresh={fetchTerceros} />

            {/* Modal para crear tercero */}
            {showModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Nuevo Tercero</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                                <X className="h-6 w-6" />
                            </button>
                        </div>
                        
                        <form onSubmit={handleSubmit}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Tipo de Documento
                                </label>
                                <select 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.tipo_documento}
                                    onChange={(e) => setFormData({...formData, tipo_documento: e.target.value})}
                                    required
                                >
                                    <option value="CC">Cédula de Ciudadanía</option>
                                    <option value="NIT">NIT</option>
                                    <option value="CE">Cédula de Extranjería</option>
                                </select>
                            </div>
                            
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Número de Documento
                                </label>
                                <input 
                                    type="text" 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.numero_documento}
                                    onChange={(e) => setFormData({...formData, numero_documento: e.target.value})}
                                    required 
                                />
                            </div>
                            
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Nombre/Razón Social
                                </label>
                                <input 
                                    type="text" 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.nombre_razon_social}
                                    onChange={(e) => setFormData({...formData, nombre_razon_social: e.target.value})}
                                    required 
                                />
                            </div>
                            
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
                                <input 
                                    type="text" 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.direccion}
                                    onChange={(e) => setFormData({...formData, direccion: e.target.value})}
                                />
                            </div>
                            
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
                                <input 
                                    type="tel" 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.telefono}
                                    onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                                />
                            </div>
                            
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input 
                                    type="email" 
                                    className="w-full p-2 border border-gray-300 rounded"
                                    value={formData.email}
                                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                                />
                            </div>
                            
                            <div className="flex justify-end space-x-2">
                                <button 
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                                >
                                    Cancelar
                                </button>
                                <button 
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                                >
                                    Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TercerosPage;