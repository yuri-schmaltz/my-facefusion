import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_URL,
});

export const system = {
    health: () => api.get('/health'),
    info: () => api.get('/system/info'),
};

export const config = {
    getProcessors: () => api.get('/processors'),
    update: (data: any) => api.post('/config', data),
};

export const files = {
    upload: (file: File, type: 'source' | 'target') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);
        return api.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    preview: (path: str) => \`\${API_URL}/files/preview?path=\${encodeURIComponent(path)}\`,
};
