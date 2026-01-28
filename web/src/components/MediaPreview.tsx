import React, { useRef, useState, useEffect } from "react";
import { Upload, X, Replace, Ban, Eraser } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/services/api";

interface MediaPreviewProps {
    file: string | null;
    type: "source" | "target";
    label: string;
    onUpload: () => void;
    onClear: () => void;
    isMasking?: boolean;
    maskArea?: number[]; // [x1, y1, x2, y2]
    onMaskChange?: (area: number[]) => void;
    className?: string;
}

export const MediaPreview: React.FC<MediaPreviewProps> = ({
    file,
    type,
    label,
    onUpload,
    onClear,
    isMasking,
    maskArea,
    onMaskChange,
    className
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const mediaRef = useRef<HTMLVideoElement | HTMLImageElement>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [startPos, setStartPos] = useState<{ x: number, y: number } | null>(null);
    const [currentPos, setCurrentPos] = useState<{ x: number, y: number } | null>(null);

    const isVideo = file?.toLowerCase().endsWith('.mp4') || file?.toLowerCase().endsWith('.mov') || file?.toLowerCase().endsWith('.avi');

    const getMediaDimensions = () => {
        if (!mediaRef.current) return null;
        const media = mediaRef.current;
        if (media instanceof HTMLVideoElement) {
            return { w: media.videoWidth, h: media.videoHeight };
        } else {
            return { w: (media as HTMLImageElement).naturalWidth, h: (media as HTMLImageElement).naturalHeight };
        }
    };

    const getDisplayedRect = () => {
        if (!mediaRef.current || !containerRef.current) return null;
        const dims = getMediaDimensions();
        if (!dims) return null;

        const container = containerRef.current.getBoundingClientRect();
        const containerRatio = container.width / container.height;
        const mediaRatio = dims.w / dims.h;

        let displayedW, displayedH, offsetX, offsetY;

        if (mediaRatio > containerRatio) {
            // Limited by width
            displayedW = container.width;
            displayedH = container.width / mediaRatio;
            offsetX = 0;
            offsetY = (container.height - displayedH) / 2;
        } else {
            // Limited by height
            displayedH = container.height;
            displayedW = container.height * mediaRatio;
            offsetX = (container.width - displayedW) / 2;
            offsetY = 0;
        }

        return { w: displayedW, h: displayedH, x: offsetX, y: offsetY, scale: dims.w / displayedW };
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        if (!isMasking || !file) return;
        e.stopPropagation();
        e.preventDefault();

        const rect = containerRef.current?.getBoundingClientRect();
        if (!rect) return;

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        setIsDrawing(true);
        setStartPos({ x, y });
        setCurrentPos({ x, y });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDrawing || !startPos) return;
        e.stopPropagation();
        e.preventDefault();

        const rect = containerRef.current?.getBoundingClientRect();
        if (!rect) return;

        const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
        const y = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

        setCurrentPos({ x, y });
    };

    const handleMouseUp = (e: React.MouseEvent) => {
        if (!isDrawing || !startPos || !currentPos) return;
        e.stopPropagation();
        e.preventDefault();

        setIsDrawing(false);

        // Calculate final coords relative to media
        const displayed = getDisplayedRect();
        if (!displayed || !onMaskChange) return;

        // Get container-relative box
        let x1 = Math.min(startPos.x, currentPos.x);
        let y1 = Math.min(startPos.y, currentPos.y);
        let x2 = Math.max(startPos.x, currentPos.x);
        let y2 = Math.max(startPos.y, currentPos.y);

        // Convert to media-relative
        // 1. Subtract offset
        x1 -= displayed.x;
        y1 -= displayed.y;
        x2 -= displayed.x;
        y2 -= displayed.y;

        // 2. Scale
        x1 = Math.max(0, x1 * displayed.scale);
        y1 = Math.max(0, y1 * displayed.scale);
        x2 = Math.min(getMediaDimensions()!.w, x2 * displayed.scale);
        y2 = Math.min(getMediaDimensions()!.h, y2 * displayed.scale);

        // Pass integers
        onMaskChange([Math.round(x1), Math.round(y1), Math.round(x2), Math.round(y2)]);
    };

    // Render mask box if exists
    const renderMask = () => {
        if ((!maskArea && !isDrawing) || !isMasking || !file) return null;

        const displayed = getDisplayedRect();
        // We only render if we can calculate dimensions (requires image load)
        // This might flicker initially.
        if (!displayed) return null;

        let bx1, by1, bx2, by2;

        if (isDrawing && startPos && currentPos) {
            // Live drawing relative to container
            bx1 = Math.min(startPos.x, currentPos.x);
            by1 = Math.min(startPos.y, currentPos.y);
            bx2 = Math.max(startPos.x, currentPos.x);
            by2 = Math.max(startPos.y, currentPos.y);
        } else if (maskArea && maskArea[2] > 0) {
            // Stored backend coords (media-relative)
            bx1 = (maskArea[0] / displayed.scale) + displayed.x;
            by1 = (maskArea[1] / displayed.scale) + displayed.y;
            bx2 = (maskArea[2] / displayed.scale) + displayed.x;
            by2 = (maskArea[3] / displayed.scale) + displayed.y;
        } else {
            return null;
        }

        return (
            <div
                className="absolute border-2 border-red-500 bg-red-500/20 pointer-events-none z-10"
                style={{
                    left: bx1,
                    top: by1,
                    width: bx2 - bx1,
                    height: by2 - by1
                }}
            >
                <div className="absolute top-0 right-0 -mt-6 bg-red-600 text-white text-[9px] px-1 py-0.5 rounded font-bold">
                    REMOVE
                </div>
            </div>
        );
    };

    // Force re-render on resize/load?
    // We can allow the parent to force update or just rely on state.

    return (
        <div
            ref={containerRef}
            className={cn(
                "relative bg-neutral-900 rounded-xl border-2 border-dashed border-neutral-800 flex flex-col items-center justify-center transition-all overflow-hidden group select-none",
                file ? "border-red-500/30 bg-black/40" : "hover:border-neutral-700 hover:bg-neutral-800/50",
                isMasking && file ? "cursor-crosshair" : "cursor-pointer",
                className
            )}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => setIsDrawing(false)}
            onClick={!isMasking && !file ? onUpload : undefined}
        >
            {file ? (
                <>
                    <div className="absolute inset-0 z-0 flex items-center justify-center">
                        {isVideo ? (
                            <video
                                ref={mediaRef as any}
                                src={api.defaults.baseURL ? `${api.defaults.baseURL}/files/preview?path=${encodeURIComponent(file)}` : file} // Rough fix for preview url, assumes context
                                className="w-full h-full object-contain pointer-events-none"
                                controls={!isMasking}
                            />
                        ) : (
                            <img
                                ref={mediaRef as any}
                                src={api.defaults.baseURL ? `${api.defaults.baseURL}/files/preview?path=${encodeURIComponent(file)}` : file}
                                className="w-full h-full object-contain pointer-events-none"
                            />
                        )}
                    </div>

                    {renderMask()}

                    {/* Controls Overlay */}
                    <div className="z-20 absolute top-3 right-3 flex gap-2">
                        {isMasking && (
                            <div className="px-2 py-1.5 bg-red-600/90 text-white text-xs font-bold rounded-full shadow-lg flex items-center gap-1.5 animate-pulse border border-red-400">
                                <Eraser size={12} /> DRAW MASK
                            </div>
                        )}

                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onClear();
                            }}
                            className="p-1.5 rounded-full bg-black/50 text-white/70 hover:bg-neutral-600 hover:text-white transition-colors shadow-lg backdrop-blur-sm"
                        >
                            <X size={14} />
                        </button>
                    </div>

                    {/* File Label */}
                    <div className="z-10 absolute top-3 left-3 pointer-events-none">
                        <div
                            className="flex items-center gap-2 bg-black/40 px-2 py-1 rounded backdrop-blur-sm border border-white/5"
                        >
                            <span className="text-[10px] font-bold text-white uppercase tracking-widest truncate max-w-[150px] drop-shadow-md">
                                {file.split('/').pop()}
                            </span>
                        </div>
                    </div>
                </>
            ) : (
                <div className="flex flex-col items-center justify-center w-full h-full pointer-events-none">
                    <Upload className="text-neutral-600 mb-4 group-hover:text-red-500 transition-colors" size={32} />
                    <p className="text-sm font-bold text-neutral-400 uppercase tracking-widest">{label}</p>
                    <p className="text-[10px] text-neutral-600 mt-1 italic">Image or Video</p>
                </div>
            )}
        </div>
    );
};
