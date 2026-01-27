import React from "react";
import { Info, Volume2, HardDrive, Target, Zap, User, Users, ArrowDownAz, Filter, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/Tooltip";
import { WizardModal } from "./Wizard/WizardModal";
import { system } from "@/services/api";


interface SettingsPanelProps {
    allSettings: any;
    onUpdate: (key: string, value: any) => void;
    helpTexts: Record<string, string>;
    systemInfo?: {
        execution_providers: string[];
    };
    currentTargetPath?: string | null;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
    allSettings: settings,
    onUpdate,
    helpTexts,
    currentTargetPath
}) => {
    const [wizardOpen, setWizardOpen] = React.useState(false);
    const [activeTab, setActiveTab] = React.useState("faces");
    const [choices, setChoices] = React.useState<any>(null);

    React.useEffect(() => {
        system.getGlobalChoices().then(res => {
            setChoices(res.data);
        });
    }, []);

    const tabs = [
        { id: "faces", label: "Faces", icon: User },
        { id: "masks", label: "Masks", icon: Filter },
        { id: "output", label: "Output", icon: Volume2 },
        { id: "system", label: "System", icon: HardDrive },
    ];

    const toggleArrayItem = (key: string, item: string) => {
        const current = (settings[key] || []);
        const newer = current.includes(item)
            ? current.filter((i: string) => i !== item)
            : [...current, item];
        onUpdate(key, newer);
    };

    const handleChange = (key: string, value: any) => {
        let processedValue = value;
        if (["output_video_quality", "output_audio_volume", "output_audio_quality", "execution_thread_count", "execution_queue_count", "face_selector_age_start", "face_selector_age_end", "system_memory_limit"].includes(key)) {
            processedValue = Number(value);
        } else if (["reference_face_distance", "face_detector_score", "face_landmarker_score", "face_mask_blur", "output_video_scale"].includes(key)) {
            processedValue = parseFloat(value || 0);
        } else if (key === "watermark_remover_area_start" || key === "watermark_remover_area_end") {
            processedValue = Array.isArray(value) ? value.map(Number) : [0, 0];
        } else if (key === "face_detector_margin" || key === "face_mask_padding") {
            // Handle array of 4 numbers
            processedValue = Array.isArray(value) ? value.map(Number) : [0, 0, 0, 0];
        }
        onUpdate(key, processedValue);
    };

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
            {/* Tab Navigation */}
            <div className="flex border-b border-neutral-800 bg-neutral-950/20 shrink-0">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-3 text-[10px] font-bold uppercase tracking-wider transition-all relative",
                            activeTab === tab.id
                                ? "text-red-500 bg-red-500/5"
                                : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/30"
                        )}
                    >
                        <tab.icon size={14} />
                        <span className="hidden sm:inline">{tab.label}</span>
                        {activeTab === tab.id && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-red-500 animate-in fade-in slide-in-from-bottom-1" />
                        )}
                    </button>
                ))}
            </div>

            <div className="p-4 space-y-6 overflow-y-auto custom-scrollbar flex-1">
                {activeTab === "faces" && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300">
                        {/* Face Selector Mode */}
                        <div className="space-y-4">
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
                                        onClick={() => {
                                            handleChange("face_selector_mode", mode.id);
                                            if (mode.id === 'automatic') {
                                                setWizardOpen(true);
                                            }
                                        }}
                                        className={cn(
                                            "flex-col items-start p-3 rounded-xl border transition-all relative overflow-hidden group",
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
                        <div className="grid grid-cols-2 gap-4 pt-2">
                            <div className="space-y-3">
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
                                    {(choices?.face_selector_orders || ["large-small"]).map((o: string) => (
                                        <option key={o} value={o}>{o.replace(/-/g, ' ')}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <Target size={14} className="text-neutral-500" />
                                    <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                        Detector Model
                                    </label>
                                </div>
                                <select
                                    value={settings.face_detector_model || "yolo_face"}
                                    onChange={(e) => handleChange("face_detector_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-red-500 outline-none transition-all hover:bg-neutral-800"
                                >
                                    {(choices?.face_detector_models || ["yolo_face"]).map((m: string) => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-3">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Detector Size</label>
                                <select
                                    value={settings.face_detector_size || "640x640"}
                                    onChange={(e) => handleChange("face_detector_size", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(choices?.face_detector_set?.[settings.face_detector_model || 'yolo_face'] || ["640x640"]).map((s: string) => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-3">
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Landmarker Model</label>
                                <select
                                    value={settings.face_landmarker_model || "2dfan4"}
                                    onChange={(e) => handleChange("face_landmarker_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(choices?.face_landmarker_models || ["2dfan4"]).map((m: string) => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Face Filter */}
                        <div className="space-y-4 pt-2 pb-2 border-t border-neutral-800/50">
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

                        {/* Detection Precision */}
                        <div className="space-y-4 pt-4 border-t border-neutral-800/50">
                            <div className="flex items-center gap-2">
                                <Sparkles size={14} className="text-neutral-500" />
                                <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                    Detector Settings
                                </label>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                        <span>Detector Score</span>
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

                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Detector Angles</label>
                                <div className="flex gap-2">
                                    {[0, 90, 180, 270].map((angle) => (
                                        <button
                                            key={angle}
                                            onClick={() => toggleArrayItem("face_detector_angles", angle as any)}
                                            className={cn(
                                                "flex-1 py-1 text-[10px] font-bold rounded-md border transition-all",
                                                (settings.face_detector_angles || [0]).includes(angle)
                                                    ? "bg-red-600 border-red-500 text-white"
                                                    : "bg-neutral-800/50 border-neutral-700 text-neutral-500"
                                            )}
                                        >
                                            {angle}°
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Detector Margin (T R B L) </label>
                                <div className="grid grid-cols-4 gap-2">
                                    {[0, 1, 2, 3].map((idx) => (
                                        <input
                                            key={idx}
                                            type="number"
                                            value={(settings.face_detector_margin || [0, 0, 0, 0])[idx]}
                                            onChange={(e) => {
                                                const newMargin = [...(settings.face_detector_margin || [0, 0, 0, 0])];
                                                newMargin[idx] = Number(e.target.value);
                                                handleChange("face_detector_margin", newMargin);
                                            }}
                                            className="bg-neutral-800 border-none text-white rounded-md p-1.5 text-[10px] text-center"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "masks" && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300">
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
                                {(choices?.face_mask_types || ['box', 'occlusion', 'area', 'region']).map((type: string) => (
                                    <button
                                        key={type}
                                        onClick={() => toggleArrayItem("face_mask_types", type)}
                                        className={cn(
                                            "flex-1 px-3 py-1.5 text-xs font-medium rounded-md border transition-all truncate text-center",
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

                        {/* Mask Models */}
                        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-neutral-800/50">
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Occluder Model</label>
                                <select
                                    value={settings.face_occluder_model || "xseg_1"}
                                    onChange={(e) => handleChange("face_occluder_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(choices?.face_occluder_models || ["xseg_1"]).map((m: string) => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Parser Model</label>
                                <select
                                    value={settings.face_parser_model || "bisenet_resnet_34"}
                                    onChange={(e) => handleChange("face_parser_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(choices?.face_parser_models || ["bisenet_resnet_34"]).map((m: string) => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Face Mask Regions */}
                        <div className="space-y-3 pt-2 border-t border-neutral-800/50">
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-neutral-300 block">
                                    Face Mask Regions
                                </label>
                                <Tooltip content={helpTexts['face_mask_regions']}>
                                    <Info size={14} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {(choices?.face_mask_regions || ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']).map((region: string) => (
                                    <button
                                        key={region}
                                        onClick={() => toggleArrayItem("face_mask_regions", region)}
                                        className={cn(
                                            "px-3 py-1.5 text-[10px] font-medium rounded-md border transition-all truncate min-w-[80px] text-center",
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

                        {/* Mask Blur */}
                        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-neutral-800/50">
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                    <span>Mask Blur</span>
                                    <span className="text-red-400 font-mono">{(settings.face_mask_blur || 0.3).toFixed(2)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0" max="1" step="0.05"
                                    value={settings.face_mask_blur || 0.3}
                                    onChange={(e) => handleChange("face_mask_blur", e.target.value)}
                                    className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase text-center block">Padding (T R B L) </label>
                                <div className="grid grid-cols-4 gap-1">
                                    {[0, 1, 2, 3].map((idx) => (
                                        <input
                                            key={idx}
                                            type="number"
                                            value={(settings.face_mask_padding || [0, 0, 0, 0])[idx]}
                                            onChange={(e) => {
                                                const newPadding = [...(settings.face_mask_padding || [0, 0, 0, 0])];
                                                newPadding[idx] = Number(e.target.value);
                                                handleChange("face_mask_padding", newPadding);
                                            }}
                                            className="bg-neutral-800 border-none text-white rounded-md p-1.5 text-[10px] text-center"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "output" && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-left-2 duration-300">
                        {/* Audio Controls */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <Volume2 size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Audio Settings</span>
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Audio Encoder</label>
                                        <select
                                            value={settings.output_audio_encoder || "aac"}
                                            onChange={(e) => handleChange("output_audio_encoder", e.target.value)}
                                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                        >
                                            {(choices?.output_audio_encoders || ["aac", "libmp3lame", "libopus", "flac"]).map((enc: string) => (
                                                <option key={enc} value={enc}>{enc}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                            Audio Quality
                                            <span className="text-red-500">{settings.output_audio_quality || 80}</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="100"
                                            value={settings.output_audio_quality || 80}
                                            onChange={(e) => handleChange("output_audio_quality", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
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

                        {/* Video Controls */}
                        <div className="space-y-4 pt-4 border-t border-neutral-800">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <Sparkles size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Video Settings</span>
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                            Video Encoder
                                        </label>
                                        <select
                                            value={settings.output_video_encoder || "libx264"}
                                            onChange={(e) => handleChange("output_video_encoder", e.target.value)}
                                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                        >
                                            {(choices?.output_video_encoders || ["libx264", "libx265", "hevc_nvenc"]).map((enc: string) => (
                                                <option key={enc} value={enc}>{enc}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Video Preset</label>
                                        <select
                                            value={settings.output_video_preset || "veryfast"}
                                            onChange={(e) => handleChange("output_video_preset", e.target.value)}
                                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                        >
                                            {(choices?.output_video_presets || ["ultrafast", "superfast", "veryfast", "medium", "slow"]).map((p: string) => (
                                                <option key={p} value={p}>{p}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between items-center">
                                            <span>Video Quality</span>
                                            <span className="text-red-500 font-bold">{settings.output_video_quality || 80}%</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="100"
                                            value={settings.output_video_quality || 80}
                                            onChange={(e) => handleChange("output_video_quality", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                        />
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between items-center">
                                            <span>Scale Factor</span>
                                            <span className="text-red-500 font-bold">{settings.output_video_scale || 1.0}x</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0.25" max="4" step="0.25"
                                            value={settings.output_video_scale || 1.0}
                                            onChange={(e) => handleChange("output_video_scale", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3 pt-2">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Temp Frame Format</label>
                                    <div className="flex bg-neutral-800 rounded-lg p-0.5">
                                        {(choices?.temp_frame_formats || ['png', 'bmp', 'jpg']).map((f: string) => (
                                            <button
                                                key={f}
                                                onClick={() => handleChange("temp_frame_format", f)}
                                                className={cn(
                                                    "flex-1 py-1 text-[10px] font-bold rounded-md transition-all",
                                                    settings.temp_frame_format === f
                                                        ? "bg-red-600 text-white"
                                                        : "text-neutral-500 hover:text-neutral-300"
                                                )}
                                            >
                                                {f.toUpperCase()}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "system" && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300">
                        <div className="flex items-center gap-2 text-neutral-400">
                            <HardDrive size={16} />
                            <span className="text-xs font-bold uppercase tracking-wider">Performance & Environment</span>
                        </div>

                        <div className="grid grid-cols-1 gap-6">
                            <div className="grid grid-cols-2 gap-4">
                                {/* Execution Threads */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                            Execution Threads
                                        </label>
                                        <Tooltip content={helpTexts['execution_thread_count']}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <input
                                        type="number"
                                        min="1" max="128"
                                        value={settings.execution_thread_count || 4}
                                        onChange={(e) => handleChange("execution_thread_count", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    />
                                </div>

                                {/* Execution Queue */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                            Execution Queue
                                        </label>
                                        <Tooltip content={helpTexts['execution_queue_count']}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <input
                                        type="number"
                                        min="1" max="32"
                                        value={settings.execution_queue_count || 1}
                                        onChange={(e) => handleChange("execution_queue_count", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Memory Strategy */}
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Memory Strategy</label>
                                    <select
                                        value={settings.video_memory_strategy || "strict"}
                                        onChange={(e) => handleChange("video_memory_strategy", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    >
                                        {(choices?.video_memory_strategies || ["strict", "moderate", "tolerant"]).map((s: string) => (
                                            <option key={s} value={s}>{s}</option>
                                        ))}
                                    </select>
                                </div>
                                {/* Memory Limit */}
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                        Memory Limit
                                        <span className="text-red-500">{settings.system_memory_limit || 0} GB</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="128" step="4"
                                        value={settings.system_memory_limit || 0}
                                        onChange={(e) => handleChange("system_memory_limit", e.target.value)}
                                        className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-red-600"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-neutral-800/50">
                                {/* Log Level */}
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Log Level</label>
                                    <select
                                        value={settings.log_level || "info"}
                                        onChange={(e) => handleChange("log_level", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    >
                                        {(choices?.log_levels || ["error", "warn", "info", "debug"]).map((l: string) => (
                                            <option key={l} value={l}>{l.toUpperCase()}</option>
                                        ))}
                                    </select>
                                </div>
                                {/* Voice Extractor */}
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Voice Extractor</label>
                                    <select
                                        value={settings.voice_extractor_model || "kim_vocal_2"}
                                        onChange={(e) => handleChange("voice_extractor_model", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    >
                                        {(choices?.voice_extractor_models || ["kim_vocal_1", "kim_vocal_2"]).map((m: string) => (
                                            <option key={m} value={m}>{m}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="pt-2 border-t border-neutral-800/50">
                                <button
                                    onClick={() => handleChange("keep_temp", !settings.keep_temp)}
                                    className={cn(
                                        "w-full flex items-center justify-between p-3 rounded-lg border transition-all",
                                        settings.keep_temp
                                            ? "bg-red-600/10 border-red-500/50 text-red-500"
                                            : "bg-neutral-800 border-neutral-700 text-neutral-400"
                                    )}
                                >
                                    <span className="text-xs font-bold uppercase">Keep Temp Files</span>
                                    <div className={cn("w-10 h-5 rounded-full relative transition-colors", settings.keep_temp ? "bg-red-600" : "bg-neutral-700")}>
                                        <div className={cn("absolute top-1 w-3 h-3 bg-white rounded-full transition-all", settings.keep_temp ? "left-6" : "left-1")} />
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            <WizardModal
                isOpen={wizardOpen}
                onClose={() => setWizardOpen(false)}
                targetPath={currentTargetPath || settings.target_path || ""}
            />
        </div>
    );
};

