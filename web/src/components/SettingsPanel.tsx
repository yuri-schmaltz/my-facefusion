import React from "react";
import { Info, Volume2, HardDrive, Target, Zap, User, Users, ArrowDownAz, Filter, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/Tooltip";

const FACE_MASK_TYPES = ['box', 'occlusion', 'area', 'region'];
const FACE_MASK_REGIONS = ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip'];
const OUTPUT_VIDEO_ENCODERS = ['libx264', 'libx264rgb', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo'];
const OUTPUT_AUDIO_ENCODERS = ['aac', 'libmp3lame', 'libopus', 'libvorbis', 'flac', 'pcm_s16le', 'pcm_s24le', 'rawaudio'];


interface SettingsPanelProps {
    allSettings: any;
    onUpdate: (key: string, value: any) => void;
    helpTexts: Record<string, string>;
    systemInfo?: {
        execution_providers: string[];
    };
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
    allSettings: settings,
    onUpdate,
    helpTexts
}) => {


    const toggleArrayItem = (key: string, item: string) => {
        const current = (settings[key] || []);
        const newer = current.includes(item)
            ? current.filter((i: string) => i !== item)
            : [...current, item];
        onUpdate(key, newer);
    };

    const handleChange = (key: string, value: any) => {
        let processedValue = value;
        if (["output_video_quality", "output_audio_volume", "execution_thread_count", "execution_queue_count", "face_selector_age_start", "face_selector_age_end"].includes(key)) {
            processedValue = Number(value);
        } else if (["reference_face_distance", "face_detector_score", "face_landmarker_score"].includes(key)) {
            processedValue = parseFloat(value || 0);
        } else if (key === "watermark_remover_area_start" || key === "watermark_remover_area_end") {
            processedValue = Array.isArray(value) ? value.map(Number) : [0, 0];
        }
        onUpdate(key, processedValue);
    };

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
            <div className="p-3 space-y-4 overflow-y-auto custom-scrollbar flex-1">
                {/* Face Selector Mode */}
                <div className="space-y-4 animate-in fade-in">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                Selection Strategy
                            </label>
                            <Tooltip content={helpTexts['face_selector_mode']}>
                                <Info size={14} className="text-neutral-400 cursor-help hover:text-neutral-300 transition-colors" />
                            </Tooltip>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                        {[
                            { id: 'reference', label: 'Reference', icon: Target, desc: 'Specific target' },
                            { id: 'automatic', label: 'Automatic', icon: Zap, desc: 'Smart logic' },
                            { id: 'one', label: 'Single', icon: User, desc: 'First found' },
                            { id: 'many', label: 'Many', icon: Users, desc: 'All faces' },
                        ].map((mode) => (
                            <button
                                key={mode.id}
                                onClick={() => handleChange("face_selector_mode", mode.id)}
                                className={cn(
                                    "flex flex-col items-start p-3 rounded-xl border transition-all relative overflow-hidden group",
                                    settings.face_selector_mode === mode.id
                                        ? "bg-red-600/10 border-red-500/50 shadow-[0_0_15px_rgba(220,38,38,0.1)]"
                                        : "bg-neutral-800/30 border-neutral-700/50 hover:border-neutral-600 text-neutral-400"
                                )}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <mode.icon size={16} className={cn(settings.face_selector_mode === mode.id ? "text-red-500" : "text-neutral-500")} />
                                    <span className={cn("text-xs font-bold", settings.face_selector_mode === mode.id ? "text-white" : "text-neutral-400")}>
                                        {mode.label}
                                    </span>
                                </div>
                                <span className="text-[10px] leading-tight text-neutral-500 opacity-80">{mode.desc}</span>
                                {settings.face_selector_mode === mode.id && (
                                    <div className="absolute top-0 right-0 p-1 opacity-40">
                                        <Sparkles size={10} className="text-red-500" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Reference Options */}
                    {(settings.face_selector_mode === 'reference' || settings.face_selector_mode === 'automatic') && (
                        <div className="bg-neutral-800/20 rounded-lg p-3 border border-neutral-700/30 space-y-3 animate-in fade-in slide-in-from-top-1">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between items-center">
                                    <span>Similarity Threshold</span>
                                    <span className="text-red-400 font-mono">{(settings.reference_face_distance || 0.6).toFixed(2)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0" max="1.5" step="0.05"
                                    value={settings.reference_face_distance || 0.6}
                                    onChange={(e) => handleChange("reference_face_distance", e.target.value)}
                                    className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                />
                            </div>
                        </div>
                    )}
                </div>
                {/* Face Sorting */}
                <div className="space-y-3 pt-2 animate-in fade-in">
                    <div className="flex items-center gap-2">
                        <ArrowDownAz size={14} className="text-neutral-500" />
                        <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                            Selection Order
                        </label>
                    </div>
                    <select
                        value={settings.face_selector_order || "large-small"}
                        onChange={(e) => handleChange("face_selector_order", e.target.value)}
                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all hover:bg-neutral-800"
                    >
                        <option value="large-small">Largest to Smallest</option>
                        <option value="small-large">Smallest to Largest</option>
                        <option value="left-right">Left to Right</option>
                        <option value="right-left">Right to Left</option>
                        <option value="top-bottom">Top to Bottom</option>
                        <option value="bottom-top">Bottom to Top</option>
                        <option value="best-worst">Best Score to Worst</option>
                        <option value="worst-best">Worst Score to Best</option>
                    </select>
                </div>

                {/* Face Filter */}
                <div className="space-y-4 pt-2 pb-2 border-t border-neutral-800/50 animate-in fade-in">
                    <div className="flex items-center gap-2">
                        <Filter size={14} className="text-neutral-500" />
                        <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                            Content Filtering
                        </label>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        {/* Gender Filter */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-neutral-500 uppercase">Gender</label>
                            <div className="flex bg-neutral-800 rounded-lg p-0.5">
                                {[
                                    { id: '', label: 'All' },
                                    { id: 'male', label: 'Male' },
                                    { id: 'female', label: 'Female' }
                                ].map((g) => (
                                    <button
                                        key={g.id}
                                        onClick={() => handleChange("face_selector_gender", g.id)}
                                        className={cn(
                                            "flex-1 py-1 text-[10px] font-bold rounded-md transition-all",
                                            settings.face_selector_gender === g.id
                                                ? "bg-red-600 text-white"
                                                : "text-neutral-500 hover:text-neutral-300"
                                        )}
                                    >
                                        {g.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Race Filter */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-neutral-500 uppercase">Race</label>
                            <select
                                value={settings.face_selector_race || ""}
                                onChange={(e) => handleChange("face_selector_race", e.target.value)}
                                className="w-full bg-neutral-800 border-none text-neutral-400 rounded-lg p-1.5 text-[10px] focus:ring-1 focus:ring-red-500 outline-none"
                            >
                                <option value="">All Ethnicities</option>
                                <option value="white">White</option>
                                <option value="black">Black</option>
                                <option value="latino">Latino</option>
                                <option value="asian">Asian</option>
                                <option value="indian">Indian</option>
                                <option value="arabic">Arabic</option>
                            </select>
                        </div>
                    </div>

                    {/* Age Range */}
                    <div className="space-y-2">
                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                            <span>Target Age Range</span>
                            <span className="text-neutral-300">{settings.face_selector_age_start} - {settings.face_selector_age_end} years</span>
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="number"
                                value={settings.face_selector_age_start || 0}
                                onChange={(e) => handleChange("face_selector_age_start", e.target.value)}
                                className="w-full bg-neutral-800/50 border border-neutral-700/50 text-white rounded-md p-1.5 text-xs text-center focus:ring-red-500 outline-none"
                                placeholder="Min"
                            />
                            <div className="h-px bg-neutral-700 w-4 shadow-sm" />
                            <input
                                type="number"
                                value={settings.face_selector_age_end || 100}
                                onChange={(e) => handleChange("face_selector_age_end", e.target.value)}
                                className="w-full bg-neutral-800/50 border border-neutral-700/50 text-white rounded-md p-1.5 text-xs text-center focus:ring-red-500 outline-none"
                                placeholder="Max"
                            />
                        </div>
                    </div>
                </div>

                {/* Face Detection Precision */}
                <div className="space-y-4 pt-2 border-t border-neutral-800/50 animate-in fade-in">
                    <div className="flex items-center gap-2">
                        <Sparkles size={14} className="text-neutral-500" />
                        <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                            Detection Thresholds
                        </label>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                <span>Face Detector Score</span>
                                <span className="text-red-400">{(settings.face_detector_score || 0.5).toFixed(2)}</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="1" step="0.05"
                                value={settings.face_detector_score || 0.5}
                                onChange={(e) => handleChange("face_detector_score", e.target.value)}
                                className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                <span>Landmarker Score</span>
                                <span className="text-red-400">{(settings.face_landmarker_score || 0.5).toFixed(2)}</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="1" step="0.05"
                                value={settings.face_landmarker_score || 0.5}
                                onChange={(e) => handleChange("face_landmarker_score", e.target.value)}
                                className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                            />
                        </div>
                    </div>
                </div>

                {/* Face Mask Types */}
                <div className="space-y-3 pt-2 border-t border-neutral-800/50">
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

                {/* Media Settings Section */}
                <div className="pt-3 border-t border-neutral-800 space-y-4">
                    <div className="flex items-center gap-2 text-neutral-400">
                        <Volume2 size={16} />
                        <span className="text-xs font-bold uppercase tracking-wider">Media Settings</span>
                    </div>

                    {/* Audio Controls */}
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

                    {/* Video Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Output Encoding */}
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-neutral-500 uppercase block">
                                Video Encoder
                            </label>
                            <select
                                value={settings.output_video_encoder || "libx264"}
                                onChange={(e) => handleChange("output_video_encoder", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all"
                            >
                                {OUTPUT_VIDEO_ENCODERS.map(enc => (
                                    <option key={enc} value={enc}>{enc}</option>
                                ))}
                            </select>
                        </div>

                        {/* Video Quality */}
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-neutral-500 uppercase flex justify-between items-center">
                                <span>Output Quality</span>
                                <span className="text-red-500 font-bold">{settings.output_video_quality || 80}%</span>
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={settings.output_video_quality || 80}
                                onChange={(e) => handleChange("output_video_quality", e.target.value)}
                                className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                            />
                        </div>
                    </div>
                </div>

                {/* Jobs Section */}
                <div className="pt-3 border-t border-neutral-800 space-y-4">
                    <div className="flex items-center gap-2 text-neutral-400">
                        <HardDrive size={16} />
                        <span className="text-xs font-bold uppercase tracking-wider">JOBS</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Execution Threads */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <label className="text-xs font-medium text-neutral-500 uppercase block">
                                    Execution Threads
                                </label>
                                <Tooltip content={helpTexts['execution_thread_count']}>
                                    <Info size={12} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
                            <input
                                type="number"
                                min="1"
                                max="128"
                                value={settings.execution_thread_count || 4}
                                onChange={(e) => handleChange("execution_thread_count", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all"
                            />
                        </div>

                        {/* Execution Queue */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <label className="text-xs font-medium text-neutral-500 uppercase block">
                                    Execution Queue
                                </label>
                                <Tooltip content={helpTexts['execution_queue_count']}>
                                    <Info size={12} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
                            <input
                                type="number"
                                min="1"
                                max="32"
                                value={settings.execution_queue_count || 1}
                                onChange={(e) => handleChange("execution_queue_count", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

