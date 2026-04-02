import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Axios Interceptor to attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('nl2sql_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export const registerUser = async (username, email, password) => {
    try {
        const response = await api.post('/auth/register', { username, email, password });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const loginUser = async (username, password) => {
    try {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        
        const response = await api.post('/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const connectDatabase = async (dbType, details) => {
    try {
        const response = await api.post('/connect', { db_type: dbType, details });
        return response.data; // { db_session_id: ... }
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getSchema = async (dbSessionId) => {
    try {
        const response = await api.get(`/schema?db_session_id=${dbSessionId}`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const queryDatabase = async (query, mode = 'query', dbSessionId) => {
    try {
        const payload = { 
            natural_language_query: query, 
            mode: mode,
            db_session_id: dbSessionId
        };
        const response = await api.post('/query', payload);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getHistory = async (dbSessionId) => {
    try {
        const response = await api.get(`/history/${dbSessionId}`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getAllHistory = async () => {
    try {
        const response = await api.get(`/history/all`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getProfile = async () => {
    try {
        const response = await api.get('/auth/profile');
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const updateProfile = async (updateData) => {
    try {
        const response = await api.put('/auth/profile', updateData);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};
