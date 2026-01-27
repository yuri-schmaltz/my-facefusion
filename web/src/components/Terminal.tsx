import { useEffect, useState, useRef } from "react";
import { TerminalSquare, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface TerminalProps {
    isOpen: boolean;
    onToggle: () => void;
}

export function Terminal({ isOpen, onToggle }: TerminalProps) {
    const [logs, setLogs] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const currentHost = window.location.host;
        const wsHost = import.meta.env.VITE_WS_HOST ||
            (currentHost.includes(':5173') ? currentHost.replace(':5173', ':8002') : currentHost);
        const ws = new WebSocket(`${wsProtocol}//${wsHost}/logs`);

        ws.onmessage = (event) => {
            setLogs((prev) => [...prev, event.data].slice(-100));
        };

        ws.onclose = () => console.log("WS Closed");

        return () => {
            ws.close();
        };
    }, [isOpen]);

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

export function TerminalButton({ isOpen, onToggle, className }: TerminalProps & { className?: string }) {
    return (
        <button
            onClick={onToggle}
            className={cn(
                "bg-neutral-900 border border-neutral-800 text-neutral-400 p-2.5 rounded-lg hover:border-green-500 hover:text-green-500 transition-all shadow-lg shadow-black/20",
                isOpen && "border-green-500 text-green-500",
                className
            )}
        >
            <TerminalSquare size={20} />
        </button>
    );
}
