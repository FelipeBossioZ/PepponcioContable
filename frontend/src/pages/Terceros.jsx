import React, { useState, useEffect } from 'react'; // Necesitamos hooks
import axios from 'axios'; // Necesitamos Axios
import TercerosTabla from '../components/TercerosTabla';

// ******************************************************************
// URL CORREGIDA: Apunta al prefijo base + el ViewSet de 'terceros'
// La URL final debe ser: /api/terceros/terceros/
// ******************************************************************
const API_URL = 'http://localhost:8000/api/terceros/terceros/'; 

const TercerosPage = () => {
    // Estado para almacenar los datos reales de la API
    const [terceros, setTerceros] = useState([]);
    // Estado para manejar la carga (mostraremos un mensaje bonito)
    const [loading, setLoading] = useState(true);
    // Estado para manejar errores (si Django falla)
    const [error, setError] = useState(null);

    // useEffect se ejecuta una vez para obtener los datos
    useEffect(() => {
        const fetchTerceros = async () => {
            try {
                // Petición GET a la URL corregida
                const response = await axios.get(API_URL);
                
                // Si la petición es exitosa, guardamos los datos
                setTerceros(response.data);
                setError(null);
            } catch (err) {
                // Si hay un error de conexión o CORS
                setError("Error de conexión: Verifica que Django esté corriendo y que la URL sea correcta.");
                console.error("Error al cargar terceros:", err);
            } finally {
                setLoading(false);
            }
        };

    

        fetchTerceros();
    }, []); 

    // ** Lógica de Carga y Errores **
    if (loading) {
        return <div className="p-8 text-center text-indigo-600 font-bold">Cargando datos del Backend...</div>;
    }

    if (error) {
        // Muestra el error de conexión si existe
        return <div className="p-8 text-center text-red-600 font-bold">{error}</div>;
    }
    
    // ** Renderizado de la Interfaz con datos de la API **
    return (
        <div className="p-8 bg-gray-100 min-h-screen">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-gray-800">Gestión de Terceros</h1>
                <button className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-md hover:bg-indigo-700 transition duration-150">
                    + Nuevo Tercero
                </button>
            </div>
            
            {/* Pasamos los datos REALES al componente de la tabla */}
            <TercerosTabla data={terceros} /> 
        </div>
    );
};


export default TercerosPage;