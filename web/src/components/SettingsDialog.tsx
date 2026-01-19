import { useState, useEffect } from "react";
import { config } from "@/services/api";
import { X, Save } from "lucide-react";
import { cn } from "@/lib/utils";

interface SettingsDialogProps {
    isOpen: boolean;
    onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
    const [settings, setSettings] = useState<any>({
        face_selector_mode: "reference",
        output_video_quality: 80,
        execution_providers: ["cpu"], // default fallback
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            config.getSettings().then((res) => {
                // Merge with defaults
                setSettings((prev: any) => ({ ...prev, ...res.data }));
            });
        }
    }, [isOpen]);

    const handleChange = (key: string, value: any) => {
        setSettings((prev: any) => ({ ...prev, [key]: value }));
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            // Ensure specific types
            const payload = {
                face_selector_mode: settings.face_selector_mode,
                output_video_quality: Number(settings.output_video_quality),
                settings: {
                    execution_providers: Array.isArray(settings.execution_providers) ? settings.execution_providers : [settings.execution_providers]
                }
            }
            await config.update(payload);
            onClose();
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="w-full max-w-md bg-neutral-900 border border-neutral-800 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-6 border-b border-neutral-800">
                    <h2 className="text-lg font-semibold text-white">Settings</h2>
                    <button onClick={onClose} className="text-neutral-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Face Selector Mode */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-neutral-300">
                            Face Selector Mode
                        </label>
                        <select
                            value={settings.face_selector_mode || "reference"}
                            onChange={(e) => handleChange("face_selector_mode", e.target.value)}
                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-md p-2 text-sm focus:ring-2 focus:ring-red-500 outline-none"
                        >
                            <option value="reference">Reference (One Face)</option>
                            <option value="one">One (First Found)</option>
                            <option value="many">Many (All Faces)</option>
                        </select>
                    </div>

                    {/* Video Quality */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-neutral-300 flex justify-between">
                            <span>Output Quality</span>
                            <span className="text-neutral-500">{settings.output_video_quality}%</span>
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={settings.output_video_quality || 80}
                            onChange={(e) => handleChange("output_video_quality", e.target.value)}
                            className="w-full h-2 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                        />
                    </div>

                    {/* Execution Provider */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-neutral-300">
                            Execution Provider
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            {["cuda", "cpu", "openvino", "rocm"].map((provider) => {
                                const current = settings.execution_providers || [];
                                const isSelected = current.includes(provider) || (Array.isArray(current) && current[0] === provider); // simplify list logic

                                return (
                                    <button
                                        key={provider}
                                        onClick={() => {
                                            // Creating a simplified single-select UX for now to avoid complexity
                                            handleChange("execution_providers", [provider]);
                                        }}
                                        className={cn(
                                            "px-3 py-2 text-sm rounded-md border text-center transition-all",
                                            isSelected
                                                ? "bg-red-600/20 border-red-500 text-red-500"
                                                : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                                        )}
                                    >
                                        {provider.toUpperCase()}
                                    </button>
                                )
                            })}
                        </div>
                    </div>
                </div>

                <div className="p-6 pt-0 flex justify-end">
                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="px-4 py-2 bg-white text-black font-semibold rounded-lg hover:bg-neutral-200 transition flex items-center gap-2"
                    >
                        {loading ? <span className="animate-spin">⏳</span> : <Save size={16} />}
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}
