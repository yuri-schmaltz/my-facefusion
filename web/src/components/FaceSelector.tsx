import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent } from '@/components/ui/card';
import { Tooltip } from '@/components/ui/Tooltip';
import { User, Loader2 } from 'lucide-react';

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
    onSelect?: (faceIndex: number) => void;
}

const FaceSelector: React.FC<FaceSelectorProps> = ({ targetPath, onSelect }) => {
    const [faces, setFaces] = useState<DetectedFace[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!targetPath) {
            setFaces([]);
            return;
        }

        const fetchFaces = async () => {
            setLoading(true);
            setError(null);
            try {
                // Assuming frame 0 for now for videos
                const res = await api.post('/faces/detect', { path: targetPath, frame_number: 0 });
                setFaces(res.data.faces);
            } catch (err) {
                console.error("Failed to detect faces:", err);
                setError("Could not detect faces");
            } finally {
                setLoading(false);
            }
        };

        const timer = setTimeout(fetchFaces, 500); // Debounce
        return () => clearTimeout(timer);
    }, [targetPath]);

    if (!targetPath) return null;

    return (
        <div className="mt-4 animate-in fade-in duration-300">
            <div className="flex items-center gap-2 mb-2 text-neutral-400">
                <User size={14} />
                <span className="text-xs font-bold uppercase tracking-wider">Detected Faces</span>
                {loading && <Loader2 size={12} className="animate-spin ml-2" />}
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
