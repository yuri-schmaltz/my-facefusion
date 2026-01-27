import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface TooltipProps {
    content: string | undefined;
    children: React.ReactNode;
    className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, className }) => {
    const [isVisible, setIsVisible] = useState(false);

    if (!content) return <>{children}</>;

    return (
        <div
            className="relative inline-block"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            {children}
            {isVisible && (
                <div className={cn(
                    "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5",
                    "bg-neutral-800 text-white text-[10px] leading-tight rounded-md shadow-xl",
                    "border border-neutral-700 w-48 z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-200",
                    className
                )}>
                    {content}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-neutral-800" />
                </div>
            )}
        </div>
    );
};
