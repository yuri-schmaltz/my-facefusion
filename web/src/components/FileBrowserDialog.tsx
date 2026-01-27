
import React, { useState, useEffect } from "react";
import { Folder, File as FileIcon, ArrowUp, X, Loader2 } from "lucide-react";
import { filesystem } from "../services/api";

interface FileBrowserDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (path: string) => void;
    initialPath?: string;
    type?: "source" | "target"; // To filter extensions if needed
}

interface FileSystemItem {
    name: string;
    type: "file" | "folder";
    path: string;
    size: number;
}

const FileBrowserDialog: React.FC<FileBrowserDialogProps> = ({
    isOpen,
    onClose,
    onSelect,
    initialPath,
    type
}) => {
    const [currentPath, setCurrentPath] = useState<string>(initialPath || "");
    const [items, setItems] = useState<FileSystemItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Refined Up Logic: We need the parent from the LAST response.
    // Let's modify state to hold parent.
    const [parentPath, setParentPath] = useState<string>("");

    const loadPathRefined = async (path: string) => {
        setLoading(true);
        setError(null);
        try {
            const res = await filesystem.list(path);
            setItems(res.data.items);
            setCurrentPath(res.data.path);
            setParentPath(res.data.parent);
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || "Failed to load directory.";
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    // Override loadPath
    useEffect(() => {
        if (isOpen) loadPathRefined(initialPath || "");
    }, [isOpen]);

    // Reuse handleNavigate from previous impl
    const handleNavigate = (item: FileSystemItem) => {
        if (item.type === "folder") {
            loadPathRefined(item.path);
        } else {
            onSelect(item.path);
            onClose();
        }
    };

    const isMediaFile = (name: string) => {
        return /\.(jpg|jpeg|png|webp|mp4|mov|avi|mkv)$/i.test(name);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-neutral-800 bg-neutral-900/50">
                    <div className="flex items-center gap-3 overflow-hidden">
                        <h2 className="text-lg font-semibold text-white shrink-0">Select {type === 'source' ? 'Source' : 'Target'} File</h2>
                        <div className="h-6 w-px bg-neutral-800 mx-2"></div>
                        <span className="text-xs font-mono text-neutral-400 truncate dir-rtl" dir="rtl" title={currentPath}>
                            {currentPath || "Root"}
                        </span>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-neutral-800 rounded-lg transition-colors text-neutral-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* Toolbar */}
                <div className="flex items-center gap-2 p-2 border-b border-neutral-800 bg-neutral-900/30">
                    <button
                        onClick={() => parentPath && loadPathRefined(parentPath)}
                        disabled={!parentPath || loading}
                        className="p-2 hover:bg-neutral-800 rounded-lg text-neutral-300 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                        title={parentPath || "No parent"}
                    >
                        <ArrowUp size={18} />
                        Up
                    </button>

                    <button
                        onClick={() => loadPathRefined("/")} // Explicitly go to root
                        disabled={loading}
                        className="p-2 hover:bg-neutral-800 rounded-lg text-neutral-300 disabled:opacity-30 flex items-center gap-2 text-sm"
                    >
                        <Folder size={18} /> Root
                    </button>
                    {/* Drive shortcuts for Windows could go here */}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-full text-neutral-500 gap-3">
                            <Loader2 className="animate-spin" size={32} />
                            <p className="text-sm">Loading...</p>
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center h-full text-red-500 gap-3">
                            <p>{error}</p>
                            <button
                                onClick={() => loadPathRefined("")}
                                className="px-4 py-2 bg-neutral-800 rounded text-white text-sm hover:bg-neutral-700"
                            >
                                Go to Root
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                            {items
                                .filter(item => item.type === 'folder' || isMediaFile(item.name)) // Simple client-side filter
                                .map((item) => (
                                    <button
                                        key={item.path}
                                        onClick={() => handleNavigate(item)}
                                        className={`
                    group flex flex-col items-center justify-center p-4 rounded-xl border border-transparent 
                    transition-all duration-200 gap-3
                    ${item.type === 'folder'
                                                ? 'hover:bg-blue-500/10 hover:border-blue-500/50 text-blue-400'
                                                : 'hover:bg-emerald-500/10 hover:border-emerald-500/50 text-neutral-300 hover:text-emerald-400'
                                            }
                  `}
                                    >
                                        {item.type === 'folder' ? (
                                            <Folder size={40} className="stroke-1 group-hover:scale-110 transition-transform duration-200" />
                                        ) : (
                                            <div className="relative">
                                                <FileIcon size={40} className="stroke-1 group-hover:scale-110 transition-transform duration-200" />
                                                {/* Could put thumbnail here if server supported it */}
                                            </div>
                                        )}
                                        <span className="text-xs text-center w-full truncate px-2 font-medium">
                                            {item.name}
                                        </span>
                                    </button>
                                ))}

                            {items.length === 0 && (
                                <div className="col-span-full flex flex-col items-center justify-center py-20 text-neutral-600">
                                    <p>Folder is empty</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FileBrowserDialog;
