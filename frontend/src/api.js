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

export const queryDatabase = async (query) => {
    try {
        const response = await api.post('/query', { natural_language_query: query });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : error;
    }
};
