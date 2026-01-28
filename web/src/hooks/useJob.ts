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

            if (event.event_type === 'status_changed') {
                newState.status = event.data;
            } else if (event.event_type === 'progress') {
                newState.progress = event.data;
            } else if (event.event_type === 'log') {
                // Add log to local list (optional, might be handled by Terminal)
                // For now, let's keep it simple and not duplicate logs if Terminal handles it
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
