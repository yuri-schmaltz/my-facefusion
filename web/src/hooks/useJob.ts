import { useState, useEffect, useCallback } from 'react';
import { jobService } from '../services/JobService';
import type { JobEvent } from '../services/JobService';
import { execute } from '../services/api';

export interface JobState {
    status: 'drafted' | 'queued' | 'running' | 'completed' | 'failed' | 'canceled' | 'unknown';
    progress: number;
    logs: string[];
    jobId: string | null;
}

export function useJob(initialJobId: string | null) {
    const [job, setJob] = useState<JobState>({
        status: 'unknown',
        progress: 0,
        logs: [],
        jobId: initialJobId
    });

    const handleEvent = useCallback((event: JobEvent) => {
        setJob(prev => {
            const newState = { ...prev };

            if (event.event_type === 'job_progress') {
                newState.progress = typeof event.data === 'object' ? event.data.progress : event.data;
            } else if ([
                'job_queued',
                'job_started',
                'job_completed',
                'job_failed',
                'job_canceled'
            ].includes(event.event_type)) {
                // Map event types to status (job_started -> running, job_completed -> completed, etc.)
                const statusMap: Record<string, JobState['status']> = {
                    'job_queued': 'queued',
                    'job_started': 'running',
                    'job_completed': 'completed',
                    'job_failed': 'failed',
                    'job_canceled': 'canceled'
                };
                newState.status = statusMap[event.event_type] || prev.status;
            }
            return newState;
        });
    }, []);

    useEffect(() => {
        if (!initialJobId) return;

        // Initial fetch
        execute.getStatus(initialJobId).then(res => {
            if (res.data) {
                setJob(prev => ({
                    ...prev,
                    status: res.data.status,
                    progress: res.data.progress,
                    jobId: initialJobId
                }));
            }
        });

        // Subscribe to SSE
        const unsubscribe = jobService.subscribe(initialJobId, handleEvent);
        return () => {
            unsubscribe();
        };
    }, [initialJobId, handleEvent]);

    const stop = useCallback(async () => {
        await execute.stop();
    }, []);

    return {
        job,
        stop
    };
}
