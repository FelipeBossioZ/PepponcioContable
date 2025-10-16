import React from 'react';

// Se define la estructura de las columnas que ya conocemos por models.py
const COLUMNS = [
    { header: 'ID', accessor: 'id' },
    { header: 'Documento', accessor: 'numero_documento' },
    { header: 'Razón Social', accessor: 'nombre_razon_social' },
    { header: 'Teléfono', accessor: 'telefono' },
    { header: 'Email', accessor: 'email' },
    { header: 'Acciones', accessor: 'actions' },
];

// Datos de ejemplo para que puedas ver el diseño antes de conectarlo a la API
const mockData = [
    { id: 1, tipo_documento: 'NIT', numero_documento: '900123456', nombre_razon_social: 'Empresa A', telefono: '3001234567', email: 'contacto@empresaA.com' },
    { id: 2, tipo_documento: 'CC', numero_documento: '1018555666', nombre_razon_social: 'Juan Pérez', telefono: '3109876543', email: 'juan@perez.com' },
];

const TercerosTabla = ({ data = mockData }) => {
    return (
        <div className="bg-white shadow-xl rounded-lg overflow-hidden border border-gray-100">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        {COLUMNS.map((col, index) => (
                            <th
                                key={index}
                                className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider"
                            >
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {data.map((tercero) => (
                        <tr key={tercero.id} className="hover:bg-gray-50 transition duration-150 ease-in-out">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tercero.id}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                {tercero.tipo_documento} {tercero.numero_documento}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{tercero.nombre_razon_social}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{tercero.telefono}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{tercero.email}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <a href="#" className="text-indigo-600 hover:text-indigo-900 mr-3">Editar</a>
                                <a href="#" className="text-red-600 hover:text-red-900">Eliminar</a>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default TercerosTabla;