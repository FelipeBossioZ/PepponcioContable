// frontend/src/services/auth.js
import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = 'http://localhost:8000/api';

// Configurar axios para incluir el token en todas las peticiones
axios.interceptors.request.use(
  config => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Interceptor para refrescar token si expira
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = Cookies.get('refresh_token');
        const response = await axios.post(`${API_URL}/token/refresh/`, {
          refresh: refreshToken
        });
        
        Cookies.set('access_token', response.data.access);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
        
        return axios(originalRequest);
      } catch (refreshError) {
        // Redirigir a login si el refresh falla
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username, password) => {
    try {
      const response = await axios.post(`${API_URL}/token/`, {
        username,
        password
      });
      
      Cookies.set('access_token', response.data.access);
      Cookies.set('refresh_token', response.data.refresh);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  logout: () => {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    window.location.href = '/login';
  },
  
  isAuthenticated: () => {
    return !!Cookies.get('access_token');
  }
};