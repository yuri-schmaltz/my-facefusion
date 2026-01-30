import { useEffect, useState, useRef } from "react";
import { TerminalSquare, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface TerminalProps {
    isOpen: boolean;
    onToggle: () => void;
    jobId?: string | null;
}

import { jobService } from '../services/JobService';

export function Terminal({ isOpen, onToggle, jobId }: TerminalProps) {
    const [logs, setLogs] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Effect for SSE logs from specific Job
    useEffect(() => {
        if (!isOpen || !jobId) return;

        // Subscribe to job events mostly for logs
        // We need to import jobService here or pass logs from parent?
        // Let's import jobService.

        const unsubscribe = jobService.subscribe(jobId, (event) => {
            if (event.event_type === 'log') {
                // log event data format: { level: 'info', message: '...' }
                // or just string? Models suggest log event has data.
                // Let's assume data is the message or { message }
                const msg = typeof event.data === 'string' ? event.data : event.data.message || JSON.stringify(event.data);
                setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`].slice(-100));
            }
        });
        return unsubscribe;

    }, [isOpen, jobId]);

    // Legacy WS support or generic logs? 
    // If no jobId, maybe we want system logs? 
    // The previous WS /logs streamed ALL logs.
    // If we want to maintain that for general debugging when no job is running, we can keep it.
    // But user asked to "Add Log Viewer component (streaming logs from event bus)".
    // So prioritizing Job logs is correct.

    // Let's keep the WS as fallback if no Job ID or if we want system logs? 
    // Actually, let's replace WS with SSE for the active Job, as it's cleaner.
    // However, if the user opens terminal WITHOUT a running job, they might expect system logs.
    // For now, let's stick to Job Logs as requested.

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    if (!isOpen) return null;

    return (
        <div className="fixed bottom-20 right-4 z-40 flex flex-col items-end pointer-events-none">
            <div className="pointer-events-auto w-[32rem] h-64 bg-black/90 backdrop-blur border border-neutral-800 rounded-lg shadow-2xl flex flex-col font-mono text-xs overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
                <div className="bg-neutral-900 px-3 py-1 text-neutral-400 flex justify-between items-center border-b border-neutral-800">
                    <span>facefusion-core.log</span>
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] text-green-500">● LIVE</span>
                        <button onClick={onToggle} className="text-neutral-500 hover:text-white transition-colors">
                            <X size={14} />
                        </button>
                    </div>
                </div>
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1 text-neutral-300 custom-scrollbar">
                    {logs.length === 0 && <span className="text-neutral-600 italic">Connected to stream...</span>}
                    {logs.map((log, i) => (
                        <div key={i} className="break-all border-b border-neutral-900/50 pb-0.5">{log}</div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function TerminalButton({ isOpen, onToggle, className, isProcessing }: TerminalProps & { className?: string, isProcessing?: boolean }) {
    return (
        <button
            onClick={onToggle}
            className={cn(
                "h-full px-4 flex flex-col items-center justify-center gap-1 bg-neutral-900 border border-neutral-800 text-neutral-400 rounded-lg hover:border-green-500 hover:text-green-500 transition-all shadow-lg shadow-black/20",
                isOpen && "border-green-500 text-green-500",
                // Pulse effect when processing and not open
                (isProcessing && !isOpen) && "animate-pulse border-emerald-500/50 text-emerald-400",
                // Active looking when open
                (isOpen && isProcessing) && "border-emerald-500 text-emerald-500 bg-blue-950/20",
                className
            )}
        >
            <div className="relative">
                <TerminalSquare size={18} />
                {isProcessing && (
                    <span className="absolute -top-1 -right-1 flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                )}
            </div>
            {/* <span className="text-[10px] font-bold uppercase tracking-wider hidden sm:block">Logs</span> */}
        </button>
    );
}
