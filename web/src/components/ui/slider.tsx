import * as React from "react"
import { cn } from "@/lib/utils"

export interface SliderProps {
    value: number[]
    min: number
    max: number
    step: number
    onValueChange: (value: number[]) => void
    className?: string
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
    ({ value, min, max, step, onValueChange, className, ...props }, ref) => {
        return (
            <div className={cn("relative flex w-full touch-none select-none items-center", className)}>
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value[0]}
                    onChange={(e) => onValueChange([parseFloat(e.target.value)])}
                    className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                    ref={ref}
                    {...props}
                />
            </div>
        )
    }
)
Slider.displayName = "Slider"

export { Slider }
