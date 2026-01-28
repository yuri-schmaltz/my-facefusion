import axios from 'axios';

const API_URL = '/api';

export const api = axios.create({
    baseURL: API_URL,
});

export const system = {
    health: () => api.get('/health'),
    info: () => api.get('/system/info'),
    help: () => api.get('/system/help'),
    getGlobalChoices: () => api.get('/api/v1/choices'),
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
    getStatus: (jobId: string) => api.get(`/jobs/${jobId}`),
    preview: (payload: { path: string, time_seconds?: number, frame_number?: number }) => api.post('/preview', payload),
};

export const wizard = {
    analyze: (videoPath: string) => api.post('/api/v1/wizard/analyze', { video_path: videoPath }),
    cluster: (jobId: string, refine: boolean = false, threshold: number = 0.6) => api.post('/api/v1/wizard/cluster', { job_id: jobId, threshold, refine }),
    mergeClusters: (jobId: string, clusterIndices: number[]) => api.post('/api/v1/wizard/merge_clusters', { job_id: jobId, cluster_indices: clusterIndices }),
    uploadSource: (jobId: string, file: File) => {
        const formData = new FormData();
        formData.append('job_id', jobId);
        formData.append('file', file);
        return api.post('/api/v1/wizard/upload_source', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    assignSources: (jobId: string, assignments: Record<number, string>) => api.post('/api/v1/wizard/assignments', { job_id: jobId, assignments }),
    suggest: (jobId: string) => api.post('/api/v1/wizard/suggest', { job_id: jobId }),
    generate: (jobId: string) => api.post('/api/v1/wizard/generate', { job_id: jobId }),
    getProgress: (jobId: string) => api.get(`/api/v1/wizard/progress/${jobId}`),
};

export const jobs = {
    list: () => api.get('/api/v1/jobs'),
    getDetails: (jobId: string) => api.get(`/api/v1/jobs/${jobId}`),
    submit: (jobIds: string[]) => api.post('/api/v1/jobs/submit', { job_ids: jobIds }),
    delete: (jobIds: string[]) => api.delete('/api/v1/jobs', { data: { job_ids: jobIds } }),
    run: () => api.post('/api/v1/jobs/run'),
    status: () => api.get('/api/v1/jobs/status'),
    unqueue: (jobIds: string[]) => api.post('/api/v1/jobs/unqueue', { job_ids: jobIds }),
};

export default api;
