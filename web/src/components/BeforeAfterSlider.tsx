import React, { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface BeforeAfterSliderProps {
    beforeSrc: string;
    afterSrc: string;
    isVideo?: boolean;
    className?: string;
    onTimeUpdate?: (time: number) => void;
}

const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
    beforeSrc,
    afterSrc,
    isVideo = false,
    className,
    onTimeUpdate
}) => {
    const [value, setValue] = useState(50);
    const beforeRef = useRef<HTMLVideoElement | HTMLImageElement>(null);
    const afterRef = useRef<HTMLVideoElement | HTMLImageElement>(null);

    useEffect(() => {
        if (!isVideo) return;

        const afterVideo = afterRef.current as HTMLVideoElement | null;
        const beforeVideo = beforeRef.current as HTMLVideoElement | null;
        if (!afterVideo || !beforeVideo) return;

        const syncTime = () => {
            try {
                if (Math.abs(beforeVideo.currentTime - afterVideo.currentTime) > 0.1) {
                    beforeVideo.currentTime = afterVideo.currentTime;
                }
                onTimeUpdate?.(afterVideo.currentTime);
            } catch {
                // ignore sync errors
            }
        };

        const syncPlay = () => {
            if (afterVideo.paused) {
                beforeVideo.pause();
            } else {
                beforeVideo.play().catch(() => undefined);
            }
        };

        afterVideo.addEventListener("timeupdate", syncTime);
        afterVideo.addEventListener("play", syncPlay);
        afterVideo.addEventListener("pause", syncPlay);

        return () => {
            afterVideo.removeEventListener("timeupdate", syncTime);
            afterVideo.removeEventListener("play", syncPlay);
            afterVideo.removeEventListener("pause", syncPlay);
        };
    }, [isVideo, onTimeUpdate]);

    return (
        <div className={cn("relative w-full h-full overflow-hidden", className)}>
            <div className="absolute inset-0">
                {isVideo ? (
                    <video
                        ref={beforeRef as any}
                        src={beforeSrc}
                        className="w-full h-full object-contain"
                        muted
                        playsInline
                    />
                ) : (
                    <img ref={beforeRef as any} src={beforeSrc} className="w-full h-full object-contain" />
                )}
            </div>
            <div
                className="absolute inset-0 overflow-hidden"
                style={{ width: `${value}%` }}
            >
                {isVideo ? (
                    <video
                        ref={afterRef as any}
                        src={afterSrc}
                        className="w-full h-full object-contain"
                        controls
                        playsInline
                    />
                ) : (
                    <img ref={afterRef as any} src={afterSrc} className="w-full h-full object-contain" />
                )}
            </div>
            <div
                className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.6)]"
                style={{ left: `${value}%` }}
            />
            <input
                type="range"
                min={0}
                max={100}
                value={value}
                onChange={(e) => setValue(Number(e.target.value))}
                className="absolute inset-x-3 bottom-3 accent-emerald-500"
            />
        </div>
    );
};

export default BeforeAfterSlider;
