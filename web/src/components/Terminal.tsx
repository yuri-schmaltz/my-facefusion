import { useEffect, useState, useRef } from "react";
import { TerminalSquare, X } from "lucide-react";

export function Terminal() {
    const [logs, setLogs] = useState<string[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;

        // Dynamic WebSocket URL - works with any deployment
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // In dev mode, Vite runs on 5173, backend on 8002 - detect and adjust
        const currentHost = window.location.host;
        const wsHost = import.meta.env.VITE_WS_HOST ||
            (currentHost.includes(':5173') ? currentHost.replace(':5173', ':8002') : currentHost);
        const ws = new WebSocket(`${wsProtocol}//${wsHost}/logs`);

        ws.onmessage = (event) => {
            setLogs((prev) => [...prev, event.data].slice(-100)); // Keep last 100 lines
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

    return (
        <div className="fixed bottom-4 right-4 z-40 flex flex-col items-end pointer-events-none">
            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="pointer-events-auto bg-black border border-neutral-700 text-green-500 p-2 rounded-lg shadow-lg hover:border-green-500 mb-2 transition-all"
            >
                {isOpen ? <X size={20} /> : <TerminalSquare size={20} />}
            </button>

            {isOpen && (
                <div className="pointer-events-auto w-[32rem] h-64 bg-black/90 backdrop-blur border border-neutral-800 rounded-lg shadow-2xl flex flex-col font-mono text-xs overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
                    <div className="bg-neutral-900 px-3 py-1 text-neutral-400 flex justify-between items-center border-b border-neutral-800">
                        <span>facefusion-core.log</span>
                        <span className="text-[10px] text-green-500">● LIVE</span>
                    </div>
                    <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1 text-neutral-300">
                        {logs.length === 0 && <span className="text-neutral-600 italic">Connected to stream...</span>}
                        {logs.map((log, i) => (
                            <div key={i} className="break-all border-b border-neutral-900/50 pb-0.5">{log}</div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
