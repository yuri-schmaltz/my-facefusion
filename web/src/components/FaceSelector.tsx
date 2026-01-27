import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Tooltip } from '@/components/ui/Tooltip';
import { User, Loader2, ScanEye, RotateCw } from 'lucide-react';

interface DetectedFace {
    index: number;
    score: number;
    gender: string;
    age: number;
    race: string;
    thumbnail: string;
}

interface FaceSelectorProps {
    targetPath: string | null;
    currentTime?: number;
    onSelect?: (faceIndex: number) => void;
}

const FaceSelector: React.FC<FaceSelectorProps> = ({ targetPath, currentTime = 0, onSelect }) => {
    const [faces, setFaces] = useState<DetectedFace[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [autoScan, setAutoScan] = useState(false);

    const fetchFaces = async (time: number) => {
        if (!targetPath) return;
        setLoading(true);
        setError(null);
        try {
            const res = await api.post('/faces/detect', {
                path: targetPath,
                time_seconds: time
            });
            setFaces(res.data.faces);
        } catch (err) {
            console.error("Failed to detect faces:", err);
            setError("Could not detect faces");
        } finally {
            setLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        if (targetPath) {
            fetchFaces(0);
        } else {
            setFaces([]);
        }
    }, [targetPath]);

    // Update on scrub if auto-scan is enabled
    useEffect(() => {
        if (autoScan && targetPath && currentTime !== undefined) {
            const timer = setTimeout(() => fetchFaces(currentTime), 500);
            return () => clearTimeout(timer);
        }
    }, [currentTime, autoScan, targetPath]);

    if (!targetPath) return null;

    return (
        <div className="mt-4 animate-in fade-in duration-300">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-neutral-400">
                    <User size={14} />
                    <span className="text-xs font-bold uppercase tracking-wider">Detected Faces</span>
                    {loading && <Loader2 size={12} className="animate-spin ml-2" />}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setAutoScan(!autoScan)}
                        className={`text-[10px] px-2 py-1 rounded border flex items-center gap-1 transition-all ${autoScan
                                ? "bg-red-500/20 border-red-500 text-red-500"
                                : "bg-neutral-800 border-neutral-700 text-neutral-500 hover:text-neutral-300"
                            }`}
                        title="Auto-scan faces while scrubbing video"
                    >
                        <ScanEye size={12} /> Auto
                    </button>
                    <button
                        onClick={() => fetchFaces(currentTime || 0)}
                        className="text-[10px] bg-neutral-800 border border-neutral-700 hover:bg-neutral-700 text-neutral-300 px-2 py-1 rounded flex items-center gap-1 transition-all"
                        title="Scan current frame"
                    >
                        <RotateCw size={12} className={loading ? "animate-spin" : ""} /> Scan
                    </button>
                </div>
            </div>

            {error ? (
                <div className="text-xs text-red-500 italic px-2">{error}</div>
            ) : faces.length === 0 && !loading ? (
                <div className="text-xs text-neutral-600 italic px-2">No faces found</div>
            ) : (
                <div className="grid grid-cols-4 gap-2">
                    {faces.map((face) => (
                        <Tooltip key={face.index} content={`Age: ${face.age} | ${face.gender} | Score: ${(face.score * 100).toFixed(0)}%`}>
                            <div
                                className="relative group cursor-pointer"
                                onClick={() => onSelect?.(face.index)}
                            >
                                <div className="aspect-square rounded-lg overflow-hidden border border-neutral-800 bg-neutral-900 hover:border-red-500 transition-colors">
                                    <img
                                        src={face.thumbnail}
                                        alt={`Face ${face.index}`}
                                        className="w-full h-full object-cover"
                                    />
                                    <div className="absolute top-1 right-1 bg-black/60 text-white text-[10px] px-1 rounded backdrop-blur-sm">
                                        #{face.index}
                                    </div>
                                </div>
                            </div>
                        </Tooltip>
                    ))}
                </div>
            )}
        </div>
    );
};

export default FaceSelector;
