import axios from 'axios';

const API_URL = '/api';

export const api = axios.create({
    baseURL: API_URL,
});

export const system = {
    health: () => api.get('/health'),
    info: () => api.get('/system/info'),
    help: () => api.get('/system/help'),
    selectFile: (multiple = false, initialPath?: string) =>
        api.get(`/system/select-file?multiple=${multiple}${initialPath ? `&initial_path=${encodeURIComponent(initialPath)}` : ''}`),
};

export const processors = {
    getChoices: () => api.get('/processors/choices'),
};

export const config = {
    getProcessors: () => api.get('/processors'),
    getSettings: () => api.get('/config'),
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
    preview: (path: string) => {
        // Return URL directly for img src
        return `${API_URL}/files/preview?path=${encodeURIComponent(path)}`;
    }
};

export const filesystem = {
    list: (path?: string) => api.post('/filesystem/list', { path })
};

export const execute = {
    run: () => api.post('/run'),
    stop: () => api.post('/stop'),
    getStatus: (jobId: string) => api.get(`/jobs/status/${jobId}`),
    preview: (payload: { path: string, time_seconds?: number, frame_number?: number }) => api.post('/preview', payload),
};

export default api;
