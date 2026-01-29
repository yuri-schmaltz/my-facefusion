import * as React from "react"
import { cn } from "@/lib/utils"

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> { }

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
    ({ className, children, ...props }, ref) => {
        return (
            <select
                className={cn(
                    "flex h-8 w-full items-center justify-between rounded-md border border-neutral-800 bg-neutral-950 px-3 py-1 text-xs text-neutral-300 ring-offset-neutral-950 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 appearance-none pointer-events-auto",
                    className
                )}
                ref={ref}
                {...props}
            >
                {children}
            </select>
        )
    }
)
Select.displayName = "Select"

const SelectTrigger = ({ children, ...props }: any) => <>{children}</>
const SelectValue = ({ placeholder, ...props }: any) => <>{props.value || placeholder}</>
const SelectContent = ({ children }: any) => <>{children}</>
const SelectItem = ({ children, value, ...props }: any) => (
    <option value={value} {...props}>
        {children}
    </option>
)

const SelectGroup = ({ children, label, ...props }: any) => (
    <optgroup label={label} {...props}>
        {children}
    </optgroup>
)

const SelectLabel = ({ children }: any) => (
    <h3 className="px-2 py-1.5 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
        {children}
    </h3>
)

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem, SelectGroup, SelectLabel }
