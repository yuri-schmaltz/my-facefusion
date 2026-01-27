import { useState, useEffect } from "react";
import { config } from "@/services/api";
import { Save } from "lucide-react";
import { cn } from "@/lib/utils";

const FACE_MASK_TYPES = ['box', 'occlusion', 'area', 'region'];
const FACE_MASK_REGIONS = ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip'];
const OUTPUT_VIDEO_ENCODERS = ['libx264', 'libx264rgb', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo'];

export function SettingsPanel() {
    const [settings, setSettings] = useState<any>({
        face_selector_mode: "reference",
        face_mask_types: ["box"],
        face_mask_regions: ["skin"],
        output_video_quality: 80,
        output_video_encoder: "libx264",
        execution_providers: ["cpu"],
        execution_thread_count: 4,
        execution_queue_count: 1,
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        config.getSettings().then((res) => {
            setSettings((prev: any) => ({ ...prev, ...res.data }));
        });
    }, []);

    const handleChange = (key: string, value: any) => {
        setSettings((prev: any) => ({ ...prev, [key]: value }));
    };

    const toggleArrayItem = (key: string, item: string) => {
        setSettings((prev: any) => {
            const current = (prev[key] || []);
            const newer = current.includes(item)
                ? current.filter((i: string) => i !== item)
                : [...current, item];
            return { ...prev, [key]: newer };
        });
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const payload = {
                ...settings,
                output_video_quality: Number(settings.output_video_quality),
                execution_thread_count: Number(settings.execution_thread_count),
                execution_queue_count: Number(settings.execution_queue_count),
                settings: {
                    execution_providers: Array.isArray(settings.execution_providers) ? settings.execution_providers : [settings.execution_providers]
                }
            }

            await config.update(payload);
            // Optionally show success toast
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
            <div className="flex items-center justify-between p-6 border-b border-neutral-800 shrink-0">
                <h2 className="text-lg font-semibold text-white">Settings</h2>
                <button
                    onClick={handleSave}
                    disabled={loading}
                    className="px-4 py-2 bg-white text-black text-sm font-bold rounded-lg hover:bg-neutral-200 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? <span className="animate-spin">⏳</span> : <Save size={16} />}
                    Save
                </button>
            </div>

            <div className="p-6 space-y-8 overflow-y-auto custom-scrollbar flex-1">
                {/* Face Selector Mode */}
                <div className="space-y-3">
                    <label className="text-sm font-medium text-neutral-300 block">
                        Face Selector Mode
                    </label>
                    <select
                        value={settings.face_selector_mode || "reference"}
                        onChange={(e) => handleChange("face_selector_mode", e.target.value)}
                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none transition-all"
                    >
                        <option value="reference">Reference (One Face)</option>
                        <option value="one">One (First Found)</option>
                        <option value="many">Many (All Faces)</option>
                    </select>
                </div>

                {/* Face Mask Types */}
                <div className="space-y-3">
                    <label className="text-sm font-medium text-neutral-300 block">
                        Face Mask Types
                    </label>
                    <div className="flex flex-wrap gap-2">
                        {FACE_MASK_TYPES.map((type) => (
                            <button
                                key={type}
                                onClick={() => toggleArrayItem("face_mask_types", type)}
                                className={cn(
                                    "px-3 py-1.5 text-xs font-medium rounded-md border transition-all",
                                    (settings.face_mask_types || []).includes(type)
                                        ? "bg-red-600 border-red-500 text-white"
                                        : "bg-neutral-800/50 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                                )}
                            >
                                {type}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Face Mask Regions */}
                <div className="space-y-3">
                    <label className="text-sm font-medium text-neutral-300 block">
                        Face Mask Regions
                    </label>
                    <div className="flex flex-wrap gap-2">
                        {FACE_MASK_REGIONS.map((region) => (
                            <button
                                key={region}
                                onClick={() => toggleArrayItem("face_mask_regions", region)}
                                className={cn(
                                    "px-3 py-1.5 text-xs font-medium rounded-md border transition-all",
                                    (settings.face_mask_regions || []).includes(region)
                                        ? "bg-red-600 border-red-500 text-white"
                                        : "bg-neutral-800/50 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                                )}
                            >
                                {region}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Output Encoding */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Video Encoder
                        </label>
                        <select
                            value={settings.output_video_encoder || "libx264"}
                            onChange={(e) => handleChange("output_video_encoder", e.target.value)}
                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none transition-all"
                        >
                            {OUTPUT_VIDEO_ENCODERS.map(enc => (
                                <option key={enc} value={enc}>{enc}</option>
                            ))}
                        </select>
                    </div>

                    {/* Video Quality */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 flex justify-between items-center">
                            <span>Output Quality</span>
                            <span className="text-red-500 font-bold">{settings.output_video_quality || 80}%</span>
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
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Execution Threads */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Execution Threads
                        </label>
                        <input
                            type="number"
                            min="1"
                            max="128"
                            value={settings.execution_thread_count || 4}
                            onChange={(e) => handleChange("execution_thread_count", e.target.value)}
                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none transition-all"
                        />
                    </div>

                    {/* Execution Queue */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Execution Queue
                        </label>
                        <input
                            type="number"
                            min="1"
                            max="32"
                            value={settings.execution_queue_count || 1}
                            onChange={(e) => handleChange("execution_queue_count", e.target.value)}
                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none transition-all"
                        />
                    </div>
                </div>

                {/* Execution Provider */}
                <div className="space-y-3">
                    <label className="text-sm font-medium text-neutral-300 block">
                        Execution Provider
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {["cuda", "cpu", "openvino", "rocm"].map((provider) => {
                            const current = settings.execution_providers || [];
                            const isSelected = current.includes(provider);

                            return (
                                <button
                                    key={provider}
                                    onClick={() => {
                                        toggleArrayItem("execution_providers", provider);
                                    }}
                                    className={cn(
                                        "px-3 py-2 text-sm font-medium rounded-lg border text-center transition-all",
                                        isSelected
                                            ? "bg-red-600/20 border-red-500 text-red-500"
                                            : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300"
                                    )}
                                >
                                    {provider.toUpperCase()}
                                </button>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
