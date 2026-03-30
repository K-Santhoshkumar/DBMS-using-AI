import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const connectDatabase = async (dbType, details) => {
    try {
        const response = await api.post('/connect', { db_type: dbType, details });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getSchema = async () => {
    try {
        const response = await api.get('/schema');
        return response.data; // { schema: {...} }
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const queryDatabase = async (query, mode = 'query', sessionId = null) => {
    try {
        const payload = { 
            natural_language_query: query, 
            mode: mode 
        };
        if (sessionId) {
            payload.session_id = sessionId;
        }
        const response = await api.post('/query', payload);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getModelInfo = async () => {
    try {
        const response = await api.get('/model-info');
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const getHistory = async (sessionId) => {
    try {
        const response = await api.get(`/history/${sessionId}`);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};

export const submitFeedback = async (feedbackData) => {
    try {
        const response = await api.post('/feedback', feedbackData);
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};
