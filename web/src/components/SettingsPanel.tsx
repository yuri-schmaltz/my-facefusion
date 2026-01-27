import { useState, useEffect } from "react";
import { config } from "@/services/api";
import { Info, Volume2, HardDrive } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/Tooltip";

const FACE_MASK_TYPES = ['box', 'occlusion', 'area', 'region'];
const FACE_MASK_REGIONS = ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip'];
const OUTPUT_VIDEO_ENCODERS = ['libx264', 'libx264rgb', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo'];
const OUTPUT_AUDIO_ENCODERS = ['aac', 'libmp3lame', 'libopus', 'libvorbis', 'flac', 'pcm_s16le', 'pcm_s24le', 'rawaudio'];

interface SettingsPanelProps {
    systemInfo: any;
    helpTexts: Record<string, string>;
}

export function SettingsPanel({ systemInfo, helpTexts }: SettingsPanelProps) {
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

    useEffect(() => {
        config.getSettings().then((res) => {
            setSettings((prev: any) => ({ ...prev, ...res.data }));
        });
    }, []);

    const updateBackend = (newSettings: any) => {
        const payload = {
            ...newSettings,
            output_video_quality: Number(newSettings.output_video_quality),
            execution_thread_count: Number(newSettings.execution_thread_count),
            execution_queue_count: Number(newSettings.execution_queue_count),
            settings: {
                execution_providers: Array.isArray(newSettings.execution_providers) ? newSettings.execution_providers : [newSettings.execution_providers]
            }
        };
        config.update(payload).catch(console.error);
    };

    const handleChange = (key: string, value: any) => {
        const newSettings = { ...settings, [key]: value };
        setSettings(newSettings);
        updateBackend(newSettings);
    };

    const toggleArrayItem = (key: string, item: string) => {
        const current = (settings[key] || []);
        const newer = current.includes(item)
            ? current.filter((i: string) => i !== item)
            : [...current, item];

        const newSettings = { ...settings, [key]: newer };
        setSettings(newSettings);
        updateBackend(newSettings);
    };

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
            {/* Header removed for cleaner UI with auto-save */}

            <div className="p-6 space-y-8 overflow-y-auto custom-scrollbar flex-1">
                {/* Face Selector Mode */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Face Selector Mode
                        </label>
                        <Tooltip content={helpTexts['face_selector_mode']}>
                            <Info size={14} className="text-neutral-500 cursor-help" />
                        </Tooltip>
                    </div>
                    <select
                        value={settings.face_selector_mode || "reference"}
                        onChange={(e) => handleChange("face_selector_mode", e.target.value)}
                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none transition-all"
                    >
                        <option value="reference">Reference (One Face)</option>
                        <option value="automatic">Automatic (Smart)</option>
                        <option value="one">One (First Found)</option>
                        <option value="many">Many (All Faces)</option>
                    </select>
                </div>

                {/* Face Mask Types */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Face Mask Types
                        </label>
                        <Tooltip content={helpTexts['face_mask_types']}>
                            <Info size={14} className="text-neutral-500 cursor-help" />
                        </Tooltip>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {FACE_MASK_TYPES.map((type) => (
                            <button
                                key={type}
                                onClick={() => toggleArrayItem("face_mask_types", type)}
                                className={cn(
                                    "flex-1 px-3 py-1.5 text-xs font-medium rounded-md border transition-all truncate",
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
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Face Mask Regions
                        </label>
                        <Tooltip content={helpTexts['face_mask_regions']}>
                            <Info size={14} className="text-neutral-500 cursor-help" />
                        </Tooltip>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {FACE_MASK_REGIONS.map((region) => (
                            <button
                                key={region}
                                onClick={() => toggleArrayItem("face_mask_regions", region)}
                                className={cn(
                                    "flex-1 px-3 py-1.5 text-xs font-medium rounded-md border transition-all truncate min-w-[100px] text-center",
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

                {/* Audio Settings Section */}
                <div className="pt-4 border-t border-neutral-800 space-y-6">
                    <div className="flex items-center gap-2 text-neutral-400">
                        <Volume2 size={16} />
                        <span className="text-xs font-bold uppercase tracking-wider">Audio Settings</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-neutral-500 uppercase">Audio Encoder</label>
                            <select
                                value={settings.output_audio_encoder || "aac"}
                                onChange={(e) => handleChange("output_audio_encoder", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all"
                            >
                                {OUTPUT_AUDIO_ENCODERS.map(enc => (
                                    <option key={enc} value={enc}>{enc}</option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-neutral-500 uppercase flex justify-between">
                                Audio Volume
                                <span className="text-neutral-300">{settings.output_audio_volume || 100}%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="200"
                                value={settings.output_audio_volume || 100}
                                onChange={(e) => handleChange("output_audio_volume", e.target.value)}
                                className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                            />
                        </div>
                    </div>
                </div>

                {/* Execution / Jobs Section */}
                <div className="pt-4 border-t border-neutral-800 space-y-6">
                    <div className="flex items-center gap-2 text-neutral-400">
                        <HardDrive size={16} />
                        <span className="text-xs font-bold uppercase tracking-wider">Engine & Jobs</span>
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
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-neutral-300 block">
                                    Execution Threads
                                </label>
                                <Tooltip content={helpTexts['execution_thread_count']}>
                                    <Info size={14} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
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
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-neutral-300 block">
                                    Execution Queue
                                </label>
                                <Tooltip content={helpTexts['execution_queue_count']}>
                                    <Info size={14} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
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
                </div>


            </div>
        </div>
    );
}
