import React from "react";
import { Info, Volume2, HardDrive, Target, Zap, User, Users, ArrowDownAz, Filter, Sparkles, Briefcase, Trash2, CheckSquare, Square, Play, RefreshCw, Rocket, Undo2, X, Eye, FileText, Clock, Cpu, Bug, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/Tooltip";
import { WizardModal } from "./Wizard/WizardModal";
import { jobs as jobsApi } from "@/services/api";
import { useToast } from '@/components/ui/ToastContext';
import { usePresets } from '@/hooks/usePresets';
import { FolderDown, SaveAll } from 'lucide-react';


interface SettingsPanelProps {
    settings: Record<string, any>;
    choices: Record<string, any>;
    helpTexts?: Record<string, string>;
    systemInfo: {
        name: string;
        version: string;
        execution_providers: string[];
        execution_devices: string[];
        cpu_count?: number;
    } | null;
    systemMetrics?: {
        cpu_percent?: number;
        memory_percent?: number;
        memory_used?: number;
        memory_total?: number;
        gpu?: {
            utilization?: number;
            memory_used?: number;
            memory_total?: number;
            name?: string;
        } | null;
    } | null;
    onChange: (key: string, value: any) => void;
    currentTargetPath?: string | null;
    activeProcessors: string[];
    projectName: string;
    projectList: Array<{ name: string; updated_at?: string; size?: number }>;
    autoSaveProject: boolean;
    onProjectNameChange: (value: string) => void;
    onProjectSave: () => void;
    onProjectLoad: (name: string) => void;
    onProjectRefresh: () => void;
    onAutoSaveProjectChange: (value: boolean) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
    settings,
    choices,
    helpTexts = {},
    systemInfo,
    systemMetrics,
    onChange,
    currentTargetPath,
    activeProcessors,
    projectName,
    projectList,
    autoSaveProject,
    onProjectNameChange,
    onProjectSave,
    onProjectLoad,
    onProjectRefresh,
    onAutoSaveProjectChange
}) => {
    const { addToast } = useToast();
    const { presets, savePreset, loadPreset, deletePreset } = usePresets(settings, (newSettings) => {
        Object.entries(newSettings).forEach(([key, val]) => onChange(key, val));
    });

    const [newPresetName, setNewPresetName] = React.useState("");

    const [wizardOpen, setWizardOpen] = React.useState(false);
    const [activeTab, setActiveTab] = React.useState<string>("faces");

    const tabs = [
        { id: "faces", label: "Faces", icon: User },
        { id: "masks", label: "Máscaras", icon: Filter },
        { id: "output", label: "Saída", icon: Volume2 },
        { id: "jobs", label: "Tarefas", icon: Briefcase },
        { id: "system", label: "Sistema", icon: HardDrive },
    ];

    // Jobs tab state
    const [jobsList, setJobsList] = React.useState<any[]>([]);
    const [selectedJobs, setSelectedJobs] = React.useState<Set<string>>(new Set());
    const [isLoadingJobs, setIsLoadingJobs] = React.useState(false);

    const loadJobs = React.useCallback(async () => {
        setIsLoadingJobs(true);
        try {
            const res = await jobsApi.list();
            setJobsList(res.data.jobs || []);
        } catch (err) {
            console.error("Failed to load jobs", err);
        } finally {
            setIsLoadingJobs(false);
        }
    }, []);

    React.useEffect(() => {
        if (activeTab === "jobs") {
            loadJobs();
        }
    }, [activeTab, loadJobs]);

    const toggleJobSelection = (jobId: string) => {
        setSelectedJobs(prev => {
            const newSet = new Set(prev);
            if (newSet.has(jobId)) {
                newSet.delete(jobId);
            } else {
                newSet.add(jobId);
            }
            return newSet;
        });
    };

    const selectAllJobs = () => {
        setSelectedJobs(new Set(jobsList.filter((j: any) => j.status === 'drafted' || j.status === 'queued').map((j: any) => j.id)));
    };

    const deselectAllJobs = () => {
        setSelectedJobs(new Set());
    };

    const unqueueSelectedJobs = async () => {
        const queuedSelected = Array.from(selectedJobs).filter(id =>
            jobsList.find(j => j.id === id && j.status === 'queued')
        );
        if (queuedSelected.length === 0) return;
        try {
            await jobsApi.unqueue(queuedSelected);
            addToast(`↩️ ${queuedSelected.length} job(s) returned to drafted!`, 'info');
            setSelectedJobs(new Set());
            loadJobs();
        } catch (err) {
            console.error("Failed to unqueue jobs", err);
            addToast("Failed to unqueue jobs", 'error');
        }
    };

    const submitSelectedJobs = async () => {
        if (selectedJobs.size === 0) return;
        try {
            await jobsApi.submit(Array.from(selectedJobs));
            addToast(`✅ ${selectedJobs.size} job(s) submitted to queue!`, 'success');
            setSelectedJobs(new Set());
            loadJobs();
        } catch (err) {
            console.error("Failed to submit jobs", err);
            addToast("Failed to submit jobs", 'error');
        }
    };

    const deleteSelectedJobs = async () => {
        if (selectedJobs.size === 0) return;
        if (!confirm(`Delete ${selectedJobs.size} job(s)?`)) return;
        try {
            await jobsApi.delete(Array.from(selectedJobs));
            addToast(`🗑️ ${selectedJobs.size} job(s) deleted!`, 'success');
            setSelectedJobs(new Set());
            loadJobs();
        } catch (err) {
            console.error("Failed to delete jobs", err);
            addToast("Failed to delete jobs", 'error');
        }
    };

    const runQueuedJobs = async () => {
        const queuedCount = jobsList.filter(j => j.status === 'queued').length;
        if (queuedCount === 0) {
            addToast("No queued jobs to run", 'warning');
            return;
        }
        try {
            const res = await jobsApi.run();
            addToast(`🚀 Started processing ${res.data.jobs_started || queuedCount} job(s)!`, 'success');
            loadJobs();
        } catch (err) {
            console.error("Failed to run queue", err);
            addToast("Failed to start queue processing", 'error');
        }
    };

    const updateJobPriority = async (jobId: string, priority: number) => {
        try {
            await jobsApi.setPriority(jobId, priority);
            loadJobs();
        } catch (err) {
            console.error("Failed to update priority", err);
            addToast("Falha ao atualizar prioridade", 'error');
        }
    };

    // Job Details Modal state
    const [selectedJobDetails, setSelectedJobDetails] = React.useState<any>(null);


    const viewJobDetails = async (jobId: string) => {
        try {
            const res = await jobsApi.getDetails(jobId);
            setSelectedJobDetails(res.data);
        } catch (err) {
            console.error("Failed to load job details", err);
            addToast("Failed to load job details", 'error');
        }
    };

    const closeJobDetails = () => {
        setSelectedJobDetails(null);
    };

    const toggleExecutionProvider = (item: string) => {
        const current = (settings.execution_providers || []);
        const newer = current.includes(item)
            ? current.filter((i: string) => i !== item)
            : [...current, item];

        // Ensure at least 'cpu' is always there if nothing else
        if (newer.length === 0) newer.push('cpu');

        onChange('execution_providers', newer);
    };

    const toggleArrayItem = (key: string, item: string) => {
        const current = (settings[key] || []);
        const newer = current.includes(item)
            ? current.filter((i: string) => i !== item)
            : [...current, item];
        onChange(key, newer);
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
        onChange(key, processedValue);
    };

    const formatDuration = (seconds?: number | null) => {
        if (!seconds || seconds <= 0) return "-";
        const total = Math.round(seconds);
        const hrs = Math.floor(total / 3600);
        const mins = Math.floor((total % 3600) / 60);
        const secs = total % 60;
        if (hrs > 0) return `${hrs}h ${mins}m`;
        if (mins > 0) return `${mins}m ${secs}s`;
        return `${secs}s`;
    };

    const completedDurations = jobsList
        .filter((job: any) => job.duration_seconds)
        .map((job: any) => job.duration_seconds as number);
    const averageDuration = completedDurations.length
        ? completedDurations.reduce((a: number, b: number) => a + b, 0) / completedDurations.length
        : 0;

    const queuedJobsSorted = jobsList
        .filter((job: any) => job.status === 'queued')
        .sort((a: any, b: any) => {
            if ((b.priority || 0) === (a.priority || 0)) {
                return (a.date_created || '').localeCompare(b.date_created || '');
            }
            return (b.priority || 0) - (a.priority || 0);
        });

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
            {/* Tab Navigation */}
            <div className="flex border-b border-neutral-800 bg-neutral-950/20 shrink-0">
                {tabs.map((tab: any) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-2 py-3 text-[10px] font-bold uppercase tracking-wider transition-all relative",
                            activeTab === tab.id
                                ? "text-emerald-500 bg-emerald-500/5"
                                : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/30"
                        )}
                    >
                        <tab.icon size={14} />
                        <span className="hidden sm:inline">{tab.label}</span>
                        {activeTab === tab.id && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 animate-in fade-in slide-in-from-bottom-1" />
                        )}
                    </button>
                ))}
            </div>

            <div className="p-1.5 space-y-2 overflow-y-auto custom-scrollbar flex-1">
                {activeTab === "faces" && (
                    <div className="space-y-2 animate-in fade-in slide-in-from-left-2 duration-300">
                        {/* Face Selector Mode */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                        Estratégia de Seleção
                                    </label>
                                    <Tooltip content={helpTexts['face_selector_mode']}>
                                        <Info size={14} className="text-neutral-400 cursor-help hover:text-neutral-300 transition-colors" />
                                    </Tooltip>
                                </div>
                            </div>

                            <div className="space-y-1.5 mt-1">
                                {/* Top Row: Reference, Single, Many */}
                                <div className="toggle-group">
                                    {[
                                        { id: 'reference', label: 'Referência', icon: Target },
                                        { id: 'one', label: 'Único', icon: User },
                                        { id: 'many', label: 'Muitos', icon: Users },
                                    ].map((mode) => (
                                        <button
                                            key={mode.id}
                                            onClick={() => handleChange("face_selector_mode", mode.id)}
                                            className={cn(
                                                "toggle-group-item",
                                                settings.face_selector_mode === mode.id && "active"
                                            )}
                                        >
                                            <mode.icon size={11} />
                                            <span>{mode.label}</span>
                                        </button>
                                    ))}
                                </div>

                                {/* Bottom Row: Automatic */}
                                <div className="toggle-group">
                                    <button
                                        onClick={() => {
                                            handleChange("face_selector_mode", 'automatic');
                                            setWizardOpen(true);
                                        }}
                                        className={cn(
                                            "toggle-group-item",
                                            settings.face_selector_mode === 'automatic' && "active"
                                        )}
                                    >
                                        <Zap size={11} />
                                        <span>Automático</span>
                                    </button>
                                </div>
                            </div>

                            {/* Reference Options */}
                            {(settings.face_selector_mode === 'reference' || settings.face_selector_mode === 'automatic') && (
                                <div className="section-glass space-y-1 animate-in fade-in slide-in-from-top-1 mt-2">
                                    <div className="space-y-1">
                                        <label className="text-[9px] font-bold text-neutral-500 uppercase flex justify-between items-center">
                                            <span>Limite de Similaridade</span>
                                            <span className="text-emerald-400 font-mono">{(settings.reference_face_distance || 0.6).toFixed(2)}</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="1.5" step="0.05"
                                            value={settings.reference_face_distance || 0.6}
                                            onChange={(e) => handleChange("reference_face_distance", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600 block"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Face Sorting */}
                        <div className="space-y-1.5 pt-1">
                            <div className="grid grid-cols-2 gap-2">
                                <div className="space-y-1.5">
                                    <div className="flex items-center gap-2">
                                        <ArrowDownAz size={12} className="text-neutral-500" />
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
                                            Ordem de Seleção
                                        </label>
                                    </div>
                                    <select
                                        value={settings.face_selector_order || "large-small"}
                                        onChange={(e) => handleChange("face_selector_order", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-1.5 text-xs focus:ring-1 focus:ring-emerald-500 outline-none transition-all hover:bg-neutral-800"
                                    >
                                        {(choices?.face_selector_orders || ["large-small", "small-large", "top-bottom", "bottom-top", "left-right", "right-left"]).map((order: string) => (
                                            <option key={order} value={order}>
                                                {order.replace(/-/g, ' ').toUpperCase()}
                                                {order === 'large-small' ? ' [Recomendado]' : ''}
                                            </option>
                                        ))}</select>
                                </div>

                                <div className="space-y-1.5">
                                    <div className="flex items-center gap-2">
                                        <Target size={12} className="text-neutral-500" />
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
                                            Modelo de Detecção
                                        </label>
                                    </div>
                                    <select
                                        value={settings.face_detector_model || "yolo_face"}
                                        onChange={(e) => handleChange("face_detector_model", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-1.5 text-xs focus:ring-1 focus:ring-emerald-500 outline-none transition-all hover:bg-neutral-800"
                                    >
                                        {(() => {
                                            const modelHints: Record<string, string> = {
                                                "yolo": "Padrão • Recomendado",
                                                "scrfd": "Ultra Rápido",
                                                "retinaface": "Máxima Precisão",
                                                "yunet": "Leve",
                                                "many": "Detector Universal"
                                            };
                                            const getHint = (n: string) => {
                                                const lower = n.toLowerCase();
                                                for (const [k, h] of Object.entries(modelHints)) {
                                                    if (lower.includes(k)) return ` [${h}]`;
                                                }
                                                return "";
                                            };
                                            const format = (n: string) => n.replace(/_/g, ' ').toUpperCase() + getHint(n);
                                            const items = choices?.face_detector_models || ["yolo_face"];
                                            const groups: Record<string, string[]> = { "Main Detectors": [], "Special": [] };
                                            items.forEach((m: string) => {
                                                if (m === 'many') groups["Special"].push(m);
                                                else groups["Main Detectors"].push(m);
                                            });
                                            return Object.entries(groups).map(([label, models]: [string, string[]]) => models.length > 0 && (
                                                <optgroup key={label} label={label} className="bg-neutral-900 text-neutral-500 font-bold text-[10px] uppercase">
                                                    {models.map((m: string) => <option key={m} value={m} className="bg-neutral-950 text-neutral-200">{format(m)}</option>)}
                                                </optgroup>
                                            ));
                                        })()}
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Tamanho do Detector</label>
                                    <select
                                        value={settings.face_detector_size || "640x640"}
                                        onChange={(e) => handleChange("face_detector_size", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-1.5 text-xs"
                                    >
                                        {(choices?.face_detector_set?.[settings.face_detector_model || 'yolo_face'] || ["640x640"]).map((s: string) => (
                                            <option key={s} value={s}>{s}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">Modelo Landmarker</label>
                                    <select
                                        value={settings.face_landmarker_model || "2dfan4"}
                                        onChange={(e) => handleChange("face_landmarker_model", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-1.5 text-xs"
                                    >
                                        {(() => {
                                            const format = (n: string) => {
                                                const name = n.replace(/2dfan4/i, '2D-FAN (4pts)').replace(/2dfan2/i, '2D-FAN (2pts)').toUpperCase();
                                                const hint = n.includes('peppa') ? ' [Engraçado • Experimental]' : n.includes('many') ? ' [Alta Precisão]' : ' [Padrão]';
                                                return name + hint;
                                            };
                                            const items = choices?.face_landmarker_models || ["2dfan4"];
                                            return items.map((m: string) => <option key={m} value={m}>{format(m)}</option>);
                                        })()}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Ensemble Detection Toggle */}
                        <div className="pt-2">
                            <button
                                onClick={() => handleChange("face_detector_ensemble", !settings.face_detector_ensemble)}
                                className={cn(
                                    "w-full flex items-center justify-between p-2 rounded-lg border transition-all h-9 px-3",
                                    settings.face_detector_ensemble
                                        ? "bg-emerald-600/10 border-emerald-500/50 shadow-[0_0_15px_rgba(37,99,235,0.1)]"
                                        : "bg-neutral-800/30 border-neutral-700/50 text-neutral-400"
                                )}
                            >
                                <div className="flex items-center gap-2">
                                    <Users size={14} className={cn(settings.face_detector_ensemble ? "text-emerald-500" : "text-neutral-500")} />
                                    <span className={cn("text-[10px] font-bold uppercase", settings.face_detector_ensemble ? "text-white" : "text-neutral-400")}>
                                        Detecção em Conjunto
                                    </span>
                                </div>
                                <div className={cn(
                                    "w-8 h-4 rounded-full relative transition-colors",
                                    settings.face_detector_ensemble ? "bg-emerald-500" : "bg-neutral-700"
                                )}>
                                    <div className={cn(
                                        "absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all",
                                        settings.face_detector_ensemble ? "left-4.5" : "left-0.5"
                                    )} style={{ left: settings.face_detector_ensemble ? '18px' : '2px' }} />
                                </div>
                            </button>
                            <p className="text-[8px] text-neutral-500 mt-1 px-1 italic">
                                Combina todos os modelos para precisão máxima (Mais lento)
                            </p>
                        </div>

                        {/* Face Filter */}
                        <div className="space-y-2 pt-2 pb-1 border-t border-neutral-800/50">
                            <div className="flex items-center gap-2">
                                <Filter size={12} className="text-neutral-500" />
                                <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
                                    Filtragem de Conteúdo
                                </label>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                {/* Gender Filter */}
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Gênero</label>
                                    <div className="toggle-group">
                                        {[
                                            { id: '', label: 'Todos' },
                                            { id: 'male', label: 'Masculino' },
                                            { id: 'female', label: 'Feminino' }
                                        ].map((g: any) => (
                                            <button
                                                key={g.id}
                                                onClick={() => handleChange("face_selector_gender", g.id)}
                                                className={cn(
                                                    "toggle-group-item",
                                                    settings.face_selector_gender === g.id && "active"
                                                )}
                                            >
                                                {g.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Race Filter */}
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Raça</label>
                                    <div className="relative">
                                        <select
                                            value={settings.face_selector_race || ""}
                                            onChange={(e) => handleChange("face_selector_race", e.target.value)}
                                            className="w-full bg-neutral-800/50 border border-neutral-700/50 text-white rounded-md pl-2 pr-6 py-1 text-xs focus:ring-1 focus:ring-emerald-500 outline-none h-7 appearance-none"
                                        >
                                            <option value="">Todas</option>
                                            <option value="white">Branco</option>
                                            <option value="black">Negro</option>
                                            <option value="latino">Latino</option>
                                            <option value="asian">Asiático</option>
                                            <option value="indian">Indiano</option>
                                            <option value="arabic">Árabe</option>
                                        </select>
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-neutral-500">
                                            <Filter size={10} strokeWidth={3} />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Age Range */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                    <span>Faixa Etária Alvo</span>
                                    <span className="text-neutral-300">{settings.face_selector_age_start} - {settings.face_selector_age_end} anos</span>
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    <input
                                        type="number"
                                        value={settings.face_selector_age_start || 0}
                                        onChange={(e) => handleChange("face_selector_age_start", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-white rounded-md p-1 text-xs text-center focus:ring-emerald-500 outline-none h-7"
                                        placeholder="Min"
                                    />
                                    <input
                                        type="number"
                                        value={settings.face_selector_age_end || 100}
                                        onChange={(e) => handleChange("face_selector_age_end", e.target.value)}
                                        className="w-full bg-neutral-800/50 border border-neutral-700/50 text-white rounded-md p-1 text-xs text-center focus:ring-emerald-500 outline-none h-7"
                                        placeholder="Max"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Detection Precision */}
                        <div className="space-y-2 pt-2 border-t border-neutral-800/50">
                            <div className="flex items-center gap-2">
                                <Sparkles size={12} className="text-neutral-500" />
                                <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
                                    Configurações do Detector
                                </label>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                        <span>Pontuação do Detector</span>
                                        <span className="text-emerald-400">{(settings.face_detector_score || 0.5).toFixed(2)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.05"
                                        value={settings.face_detector_score || 0.5}
                                        onChange={(e) => handleChange("face_detector_score", e.target.value)}
                                        className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                        <span>Pontuação Landmarker</span>
                                        <span className="text-emerald-400">{(settings.face_landmarker_score || 0.5).toFixed(2)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="1" step="0.05"
                                        value={settings.face_landmarker_score || 0.5}
                                        onChange={(e) => handleChange("face_landmarker_score", e.target.value)}
                                        className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Ângulos do Detector</label>
                                <div className="toggle-group">
                                    {[0, 90, 180, 270].map((angle: number) => (
                                        <button
                                            key={angle}
                                            onClick={() => toggleArrayItem("face_detector_angles", angle as any)}
                                            className={cn(
                                                "toggle-group-item",
                                                (settings.face_detector_angles || [0]).includes(angle) && "active"
                                            )}
                                        >
                                            {angle}°
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Margem do Detector (C D B E) </label>
                                <div className="grid grid-cols-4 gap-2">
                                    {[0, 1, 2, 3].map((idx: number) => (
                                        <input
                                            key={idx}
                                            type="number"
                                            value={(settings.face_detector_margin || [0, 0, 0, 0])[idx]}
                                            onChange={(e) => {
                                                const newMargin = [...(settings.face_detector_margin || [0, 0, 0, 0])];
                                                newMargin[idx] = Number(e.target.value);
                                                handleChange("face_detector_margin", newMargin);
                                            }}
                                            className="bg-neutral-800 border-none text-white rounded-md p-1 text-[10px] text-center h-6"
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
                                    Tipos de Máscara Facial
                                </label>
                                <Tooltip content={helpTexts['face_mask_types']}>
                                    <Info size={14} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                                {(() => {
                                    const getHint = (n: string) => {
                                        if (n === 'box') return 'Ret. Simples';
                                        if (n === 'occlusion') return 'Auto-Máscara';
                                        if (n === 'area') return 'Sel. Manual';
                                        if (n === 'region') return 'Semântica';
                                        return "";
                                    };
                                    return (choices?.face_mask_types || ['box', 'occlusion', 'area', 'region']).map((type: string) => (
                                        <button
                                            key={type}
                                            onClick={() => toggleArrayItem("face_mask_types", type)}
                                            className={cn(
                                                "flex-1 p-2 rounded-lg border transition-all flex flex-col items-center gap-0.5",
                                                (settings.face_mask_types || []).includes(type)
                                                    ? "bg-emerald-600 border-emerald-500 text-white shadow-lg shadow-blue-900/20"
                                                    : "bg-neutral-800/50 border-neutral-700/50 text-neutral-400 hover:border-neutral-600"
                                            )}
                                        >
                                            <span className="text-[10px] font-bold uppercase tracking-wider">{type}</span>
                                            <span className="text-[8px] opacity-60 font-medium">{getHint(type)}</span>
                                        </button>
                                    ));
                                })()}
                            </div>
                        </div>

                        {/* Mask Models */}
                        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-neutral-800/50">
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Modelo Oclusor</label>
                                <select
                                    value={settings.face_occluder_model || "xseg_1"}
                                    onChange={(e) => handleChange("face_occluder_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(() => {
                                        const modelHints: Record<string, string> = {
                                            "xseg_1": "Equilibrado • Rápido",
                                            "xseg_2": "Alta Qualidade",
                                            "xseg_3": "Máxima Precisão",
                                            "many": "Cobertura Universal"
                                        };
                                        const getHint = (n: string) => {
                                            const lower = n.toLowerCase();
                                            for (const [k, h] of Object.entries(modelHints)) {
                                                if (lower.includes(k)) return ` [${h}]`;
                                            }
                                            return "";
                                        };
                                        const items = choices?.face_occluder_models || ["xseg_1"];
                                        const groups: Record<string, string[]> = { "Modelos XSeg": [], "Especial": [] };
                                        items.forEach((m: string) => {
                                            if (m === 'many') groups["Special"].push(m);
                                            else groups["XSeg Models"].push(m);
                                        });
                                        return Object.entries(groups).map(([label, models]: [string, string[]]) => models.length > 0 && (
                                            <optgroup key={label} label={label} className="bg-neutral-900 text-neutral-500 font-bold text-[10px] uppercase">
                                                {models.map((m: string) => <option key={m} value={m} className="bg-neutral-950 text-neutral-200">{m.replace(/_/g, ' ').toUpperCase() + getHint(m)}</option>)}
                                            </optgroup>
                                        ));
                                    })()}
                                </select>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase">Modelo Analisador</label>
                                <select
                                    value={settings.face_parser_model || "bisenet_resnet_34"}
                                    onChange={(e) => handleChange("face_parser_model", e.target.value)}
                                    className="w-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-300 rounded-lg p-2 text-xs"
                                >
                                    {(choices?.face_parser_models || ["bisenet_resnet_34"]).map((m: string) => {
                                        const hint = m.includes('34') ? ' [Alta Precisão • Lento]' : ' [Rápido • Equilibrado]';
                                        return (
                                            <option key={m} value={m}>
                                                {m.replace(/bisenet_resnet_/i, 'BiseNet ').replace(/_/g, ' ').toUpperCase() + hint}
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>
                        </div>

                        {/* Face Mask Regions */}
                        <div className="space-y-3 pt-2 border-t border-neutral-800/50">
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-neutral-300 block">
                                    Regiões da Máscara Facial
                                </label>
                                <Tooltip content={helpTexts['face_mask_regions']}>
                                    <Info size={14} className="text-neutral-500 cursor-help" />
                                </Tooltip>
                            </div>
                            <div className="grid grid-cols-5 gap-2">
                                {(choices?.face_mask_regions || ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']).map((region: string) => (
                                    <button
                                        key={region}
                                        onClick={() => toggleArrayItem("face_mask_regions", region)}
                                        className={cn(
                                            "px-2 py-1.5 text-[10px] font-medium rounded-md border transition-all truncate text-center w-full",
                                            (settings.face_mask_regions || []).includes(region)
                                                ? "bg-emerald-600 border-emerald-500 text-white"
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
                                    <span>Desfoque da Máscara</span>
                                    <span className="text-emerald-400 font-mono">{(settings.face_mask_blur || 0.3).toFixed(2)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0" max="1" step="0.05"
                                    value={settings.face_mask_blur || 0.3}
                                    onChange={(e) => handleChange("face_mask_blur", e.target.value)}
                                    className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                />
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase text-center block">Preenchimento (C D B E) </label>
                                <div className="grid grid-cols-4 gap-1">
                                    {[0, 1, 2, 3].map((idx: number) => (
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
                                <span className="text-xs font-bold uppercase tracking-wider">Configurações de Áudio</span>
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Codificador de Áudio</label>
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
                                            Qualidade do Áudio
                                            <span className="text-emerald-500">{settings.output_audio_quality || 80}</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="100"
                                            value={settings.output_audio_quality || 80}
                                            onChange={(e) => handleChange("output_audio_quality", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                        Volume do Áudio
                                        <span className="text-neutral-300">{settings.output_audio_volume || 100}%</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="200"
                                        value={settings.output_audio_volume || 100}
                                        onChange={(e) => handleChange("output_audio_volume", e.target.value)}
                                        className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                    />
                                </div>
                                {/* Voice Extractor */}
                                <div className="space-y-3 pt-2">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Extrator de Voz</label>
                                    <select
                                        value={settings.voice_extractor_model || "kim_vocal_2"}
                                        onChange={(e) => handleChange("voice_extractor_model", e.target.value)}
                                        className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                    >
                                        {(choices?.voice_extractor_models || ["kim_vocal_1", "kim_vocal_2", "uwr_mdxnet"]).map((m: string) => {
                                            const hint = m.includes('kim_vocal_2') ? ' [Melhor Separação]' : m.includes('uwr') ? ' [Rápido • Leve]' : ' [Legado]';
                                            const label = m.replace(/_vocal_/i, ' Vocal v').replace(/uwr_mdxnet/i, 'MDX-Net (UWR)').toUpperCase();
                                            return (
                                                <option key={m} value={m}>
                                                    {label + hint}
                                                </option>
                                            );
                                        })}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Video Controls */}
                        <div className="space-y-4 pt-4 border-t border-neutral-800">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <Sparkles size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Configurações de Vídeo</span>
                            </div>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                            Codificador de Vídeo
                                        </label>
                                        <select
                                            value={settings.output_video_encoder || "libx264"}
                                            onChange={(e) => handleChange("output_video_encoder", e.target.value)}
                                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2 text-xs"
                                        >
                                            {(() => {
                                                const items = choices?.output_video_encoders || ["libx264"];
                                                const groups: Record<string, string[]> = { "Software (CPU)": [], "Hardware (GPU)": [] };
                                                items.forEach((m: string) => {
                                                    if (m.startsWith('lib')) groups["Software (CPU)"].push(m);
                                                    else groups["Hardware (GPU)"].push(m);
                                                });
                                                const getHint = (n: string) => {
                                                    if (n.includes('265') || n.includes('hevc')) return ' [Alta Eficiência]';
                                                    if (n.includes('264')) return ' [Universalmente Compatível]';
                                                    if (n.includes('nvenc')) return ' [NVIDIA Powered]';
                                                    return "";
                                                };
                                                return Object.entries(groups).map(([label, models]: [string, string[]]) => models.length > 0 && (
                                                    <optgroup key={label} label={label} className="bg-neutral-900 text-neutral-500 font-bold text-[10px] uppercase">
                                                        {models.map((m: string) => <option key={m} value={m} className="bg-neutral-950 text-neutral-200">{m.replace(/lib/i, '').replace(/_/g, ' ').toUpperCase() + getHint(m)}</option>)}
                                                    </optgroup>
                                                ));
                                            })()}
                                        </select>
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Predefinição de Vídeo</label>
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
                                            <span>Qualidade do Vídeo</span>
                                            <span className="text-emerald-500 font-bold">{settings.output_video_quality || 80}%</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="100"
                                            value={settings.output_video_quality || 80}
                                            onChange={(e) => handleChange("output_video_quality", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                        />
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between items-center">
                                            <span>Fator de Escala</span>
                                            <span className="text-emerald-500 font-bold">{settings.output_video_scale || 1.0}x</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0.25" max="4" step="0.25"
                                            value={settings.output_video_scale || 1.0}
                                            onChange={(e) => handleChange("output_video_scale", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3 pt-2">
                                    <label className="text-[10px] font-bold text-neutral-500 uppercase">Formato de Quadro Temporário</label>
                                    <div className="flex bg-neutral-800 rounded-lg p-0.5">
                                        {(choices?.temp_frame_formats || ['png', 'bmp', 'jpg']).map((f: string) => (
                                            <button
                                                key={f}
                                                onClick={() => handleChange("temp_frame_format", f)}
                                                className={cn(
                                                    "flex-1 py-1 text-[10px] font-bold rounded-md transition-all",
                                                    settings.temp_frame_format === f
                                                        ? "bg-emerald-600 text-white"
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

                {activeTab === "jobs" && (
                    <div className="flex flex-col h-full animate-in fade-in slide-in-from-left-2 duration-300">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <Briefcase size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Fila de Tarefas</span>
                                <span className="text-[10px] bg-neutral-800 px-2 py-0.5 rounded-full">{jobsList.length} tarefas</span>
                            </div>
                            <button
                                onClick={loadJobs}
                                disabled={isLoadingJobs}
                                className="p-2 hover:bg-neutral-800 rounded-lg transition-colors text-neutral-400 hover:text-white"
                            >
                                <RefreshCw size={14} className={isLoadingJobs ? "animate-spin" : ""} />
                            </button>
                        </div>

                        {/* Actions Bar */}
                        <div className="flex flex-wrap items-center gap-2 p-2 bg-neutral-800/50 rounded-lg mb-4 shrink-0">
                            <button
                                onClick={selectAllJobs}
                                className="px-3 py-1.5 text-[10px] font-bold uppercase bg-neutral-700 hover:bg-neutral-600 rounded transition-colors flex items-center gap-1.5 whitespace-nowrap"
                            >
                                <CheckSquare size={12} /> Selecionar Tudo
                            </button>
                            <button
                                onClick={deselectAllJobs}
                                className="px-3 py-1.5 text-[10px] font-bold uppercase bg-neutral-700 hover:bg-neutral-600 rounded transition-colors flex items-center gap-1.5 whitespace-nowrap"
                            >
                                <Square size={12} /> Desmarcar
                            </button>
                            <div className="flex-1 min-w-[20px]" />
                            <button
                                onClick={submitSelectedJobs}
                                disabled={selectedJobs.size === 0}
                                className={cn(
                                    "px-3 py-1.5 text-[10px] font-bold uppercase rounded transition-colors flex items-center gap-1.5 whitespace-nowrap",
                                    selectedJobs.size > 0
                                        ? "bg-green-600 hover:bg-green-500 text-white"
                                        : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
                                )}
                            >
                                <Play size={12} /> Enviar ({selectedJobs.size})
                            </button>
                            <button
                                onClick={unqueueSelectedJobs}
                                disabled={Array.from(selectedJobs).filter(id => jobsList.find(j => j.id === id && j.status === 'queued')).length === 0}
                                className={cn(
                                    "px-3 py-1.5 text-[10px] font-bold uppercase rounded transition-colors flex items-center gap-1.5 whitespace-nowrap",
                                    Array.from(selectedJobs).filter(id => jobsList.find(j => j.id === id && j.status === 'queued')).length > 0
                                        ? "bg-yellow-600 hover:bg-yellow-500 text-white"
                                        : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
                                )}
                            >
                                <Undo2 size={12} /> Remover da Fila
                            </button>
                            <button
                                onClick={deleteSelectedJobs}
                                disabled={selectedJobs.size === 0}
                                className={cn(
                                    "px-3 py-1.5 text-[10px] font-bold uppercase rounded transition-colors flex items-center gap-1.5 whitespace-nowrap",
                                    selectedJobs.size > 0
                                        ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                                        : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
                                )}
                            >
                                <Trash2 size={12} /> Excluir
                            </button>
                            <button
                                onClick={runQueuedJobs}
                                disabled={jobsList.filter(j => j.status === 'queued').length === 0}
                                className={cn(
                                    "px-3 py-1.5 text-[10px] font-bold uppercase rounded transition-colors flex items-center gap-1.5 whitespace-nowrap",
                                    jobsList.filter(j => j.status === 'queued').length > 0
                                        ? "bg-purple-600 hover:bg-purple-500 text-white"
                                        : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
                                )}
                            >
                                <Rocket size={12} /> Executar Fila ({jobsList.filter(j => j.status === 'queued').length})
                            </button>
                        </div>

                        {/* Job List - fills remaining height */}
                        <div className="flex-1 space-y-2 overflow-y-auto custom-scrollbar">
                            {isLoadingJobs ? (
                                <div className="text-center py-8 text-neutral-500">Carregando tarefas...</div>
                            ) : jobsList.length === 0 ? (
                                <div className="text-center py-8 text-neutral-500">
                                    <Briefcase size={32} className="mx-auto mb-2 opacity-30" />
                                    <p>Nenhuma tarefa na fila</p>
                                    <p className="text-xs mt-1">Use o Assistente para criar tarefas</p>
                                </div>
                            ) : (
                                jobsList.map((job: any) => {
                                    const queuedIndex = queuedJobsSorted.findIndex((q: any) => q.id === job.id);
                                    const etaSeconds = (job.status === 'queued' && averageDuration)
                                        ? (queuedIndex + 1) * averageDuration
                                        : null;
                                    const isSelected = selectedJobs.has(job.id);
                                    const statusColors: Record<string, string> = {
                                        drafted: "bg-yellow-500/20 text-yellow-500 border-yellow-500/30",
                                        queued: "bg-emerald-500/20 text-emerald-500 border-emerald-500/30",
                                        running: "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                        completed: "bg-green-500/20 text-green-500 border-green-500/30",
                                        failed: "bg-emerald-500/20 text-emerald-500 border-emerald-500/30",
                                    };
                                    return (
                                        <div
                                            key={job.id}
                                            onClick={() => (job.status === 'drafted' || job.status === 'queued') && toggleJobSelection(job.id)}
                                            className={cn(
                                                "p-3 rounded-lg border transition-all cursor-pointer",
                                                isSelected
                                                    ? "bg-emerald-600/10 border-emerald-500/50"
                                                    : "bg-neutral-800/50 border-neutral-700 hover:border-neutral-600",
                                                (job.status !== 'drafted' && job.status !== 'queued') && "opacity-60 cursor-default"
                                            )}
                                        >
                                            <div className="flex items-center gap-3">
                                                {/* Checkbox */}
                                                <div className={cn(
                                                    "w-4 h-4 rounded border-2 flex items-center justify-center transition-colors",
                                                    isSelected ? "bg-emerald-600 border-emerald-600" : "border-neutral-600",
                                                    (job.status !== 'drafted' && job.status !== 'queued') && "invisible"
                                                )}>
                                                    {isSelected && <CheckSquare size={10} className="text-white" />}
                                                </div>

                                                {/* Job Info */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-mono text-white truncate">{job.id}</span>
                                                        <span className={cn("text-[9px] px-2 py-0.5 rounded border font-bold uppercase", statusColors[job.status] || "bg-neutral-700")}>
                                                            {job.status}
                                                        </span>
                                                    </div>
                                                    {job.target_path && (
                                                        <p className="text-[10px] text-neutral-500 truncate mt-1">
                                                            {job.target_path.split('/').pop()}
                                                        </p>
                                                    )}
                                                    {job.status === 'running' && (
                                                        <p className="text-[10px] text-blue-400 mt-1">Em execução…</p>
                                                    )}
                                                </div>

                                                {/* Steps count */}
                                                <div className="text-[10px] text-neutral-500 text-right">
                                                    <div>{job.step_count} passo{job.step_count !== 1 ? 's' : ''}</div>
                                                    {etaSeconds ? (
                                                        <div className="text-[9px] text-emerald-400">ETA {formatDuration(etaSeconds)}</div>
                                                    ) : null}
                                                </div>

                                                {/* Priority */}
                                                {(job.status === 'drafted' || job.status === 'queued') ? (
                                                    <select
                                                        value={job.priority || 0}
                                                        onChange={(e) => updateJobPriority(job.id, Number(e.target.value))}
                                                        onClick={(e) => e.stopPropagation()}
                                                        className="text-[10px] bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-neutral-300"
                                                        title="Prioridade"
                                                    >
                                                        <option value={0}>Baixa</option>
                                                        <option value={5}>Normal</option>
                                                        <option value={10}>Alta</option>
                                                    </select>
                                                ) : (
                                                    <div className="text-[10px] text-neutral-500">Prio {job.priority || 0}</div>
                                                )}

                                                {/* View Details Button */}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        viewJobDetails(job.id);
                                                    }}
                                                    className="p-1.5 hover:bg-neutral-700 rounded transition-colors text-neutral-400 hover:text-white"
                                                    title="Ver Detalhes"
                                                >
                                                    <Eye size={14} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}

                {activeTab === "system" && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-left-2 duration-300 p-1">
                        {/* System Metrics */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <Cpu size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Métricas em Tempo Real</span>
                            </div>
                            <div className="bg-neutral-950/30 rounded-lg p-3 border border-neutral-800 space-y-3">
                                <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] text-neutral-400">
                                        <span>CPU</span>
                                        <span>{Math.round(systemMetrics?.cpu_percent || 0)}%</span>
                                    </div>
                                    <div className="w-full h-1 bg-neutral-800 rounded">
                                        <div
                                            className="h-1 bg-emerald-500 rounded"
                                            style={{ width: `${systemMetrics?.cpu_percent || 0}%` }}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex justify-between text-[10px] text-neutral-400">
                                        <span>Memória</span>
                                        <span>{Math.round(systemMetrics?.memory_percent || 0)}%</span>
                                    </div>
                                    <div className="w-full h-1 bg-neutral-800 rounded">
                                        <div
                                            className="h-1 bg-emerald-500 rounded"
                                            style={{ width: `${systemMetrics?.memory_percent || 0}%` }}
                                        />
                                    </div>
                                </div>
                                {systemMetrics?.gpu && (
                                    <div className="space-y-1">
                                        <div className="flex justify-between text-[10px] text-neutral-400">
                                            <span>GPU {systemMetrics.gpu.name || ''}</span>
                                            <span>{Math.round(systemMetrics.gpu.utilization || 0)}%</span>
                                        </div>
                                        <div className="w-full h-1 bg-neutral-800 rounded">
                                            <div
                                                className="h-1 bg-emerald-500 rounded"
                                                style={{ width: `${systemMetrics.gpu.utilization || 0}%` }}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Projects */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <FolderDown size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Projetos</span>
                            </div>
                            <div className="bg-neutral-950/30 rounded-lg p-3 border border-neutral-800 space-y-3">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        placeholder="Nome do projeto"
                                        value={projectName}
                                        onChange={(e) => onProjectNameChange(e.target.value)}
                                        className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 placeholder:text-neutral-600"
                                    />
                                    <button
                                        onClick={onProjectSave}
                                        className="px-3 py-1.5 text-[10px] font-bold uppercase rounded bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
                                    >
                                        Salvar
                                    </button>
                                    <button
                                        onClick={onProjectRefresh}
                                        className="px-3 py-1.5 text-[10px] font-bold uppercase rounded bg-neutral-800 text-neutral-300 hover:bg-neutral-700 transition-colors"
                                    >
                                        Atualizar
                                    </button>
                                </div>
                                <div className="flex items-center justify-between text-[10px] text-neutral-500">
                                    <span>Auto-salvar</span>
                                    <button
                                        onClick={() => onAutoSaveProjectChange(!autoSaveProject)}
                                        className={cn(
                                            "w-10 h-5 rounded-full relative transition-colors",
                                            autoSaveProject ? "bg-emerald-600" : "bg-neutral-700"
                                        )}
                                    >
                                        <div className={cn("absolute top-1 w-3 h-3 bg-white rounded-full transition-all", autoSaveProject ? "left-6" : "left-1")} />
                                    </button>
                                </div>
                                <div className="max-h-40 overflow-y-auto custom-scrollbar space-y-1">
                                    {projectList.length === 0 ? (
                                        <div className="text-[10px] text-neutral-600">Nenhum projeto salvo</div>
                                    ) : (
                                        projectList.map((project) => (
                                            <button
                                                key={project.name}
                                                onClick={() => onProjectLoad(project.name)}
                                                className="w-full text-left px-2 py-1 rounded bg-neutral-900/40 hover:bg-neutral-800 text-[10px] text-neutral-300"
                                            >
                                                <div className="flex justify-between">
                                                    <span>{project.name}</span>
                                                    <span className="text-neutral-500">{project.updated_at || ''}</span>
                                                </div>
                                            </button>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Presets */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <SaveAll size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Predefinições de Configuração</span>
                            </div>

                            <div className="bg-neutral-950/30 rounded-lg p-3 border border-neutral-800 space-y-3">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        placeholder="Nome da Predefinição (ex: Ultra Qualidade)"
                                        value={newPresetName}
                                        onChange={(e) => setNewPresetName(e.target.value)}
                                        className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 placeholder:text-neutral-600"
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') {
                                                savePreset(newPresetName);
                                                setNewPresetName("");
                                            }
                                        }}
                                    />
                                    <button
                                        onClick={() => {
                                            savePreset(newPresetName);
                                            setNewPresetName("");
                                        }}
                                        disabled={!newPresetName.trim()}
                                        className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        Salvar
                                    </button>
                                </div>

                                {presets.length === 0 ? (
                                    <div className="text-center py-4 text-neutral-600 text-[10px] italic">
                                        Nenhuma predefinição salva encontrada.
                                    </div>
                                ) : (
                                    <div className="space-y-2 max-h-[150px] overflow-y-auto custom-scrollbar pr-1">
                                        {presets.map((preset) => (
                                            <div key={preset.id} className="flex items-center justify-between bg-neutral-900 border border-neutral-800 rounded p-2 group hover:border-neutral-700 transition-colors">
                                                <div className="flex flex-col">
                                                    <span className="text-xs font-medium text-neutral-300">{preset.name}</span>
                                                    <span className="text-[9px] text-neutral-600">{new Date(preset.timestamp).toLocaleDateString()}</span>
                                                </div>
                                                <div className="flex items-center gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => loadPreset(preset.id)}
                                                        className="p-1.5 hover:bg-emerald-500/20 text-emerald-500 rounded transition-colors"
                                                        title="Carregar Predefinição"
                                                    >
                                                        <FolderDown size={14} />
                                                    </button>
                                                    <button
                                                        onClick={() => deletePreset(preset.id)}
                                                        className="p-1.5 hover:bg-red-500/20 text-red-500 rounded transition-colors"
                                                        title="Excluir Predefinição"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center gap-2 text-neutral-400">
                                <HardDrive size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">Desempenho e Ambiente</span>
                            </div>

                            <div className="grid grid-cols-1 gap-2">
                                {/* Execution Provider */}
                                <div className="space-y-1 pb-2 border-b border-neutral-800/50">
                                    <div className="flex items-center gap-2">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                            Provedor de Execução
                                        </label>
                                        <Tooltip content={helpTexts['execution_providers']}>
                                            <Info size={12} className="text-neutral-500 cursor-help" />
                                        </Tooltip>
                                    </div>
                                    <div className="grid grid-cols-3 gap-1">
                                        {["cpu", "cuda", "tensorrt", "rocm", "directml", "openvino", "coreml"].map((provider: string) => {
                                            const current = settings.execution_providers || [];
                                            const isSelected = current.includes(provider);
                                            const isAvailable = (systemInfo?.execution_providers || ['cpu']).includes(provider);

                                            const labels: Record<string, string> = {
                                                cpu: "CPU Standard",
                                                cuda: "NVIDIA CUDA",
                                                tensorrt: "NVIDIA TensorRT",
                                                rocm: "AMD ROCm",
                                                directml: "DirectML (Windows)",
                                                openvino: "Intel OpenVINO",
                                                coreml: "Apple CoreML"
                                            };


                                            return (
                                                <button
                                                    key={provider}
                                                    disabled={!isAvailable}
                                                    onClick={() => toggleExecutionProvider(provider)}
                                                    className={cn(
                                                        "flex flex-col items-center justify-center p-2 rounded-lg border text-center transition-all",
                                                        isSelected
                                                            ? "bg-emerald-600/10 border-emerald-500/50 shadow-[0_0_15px_rgba(37,99,235,0.1)]"
                                                            : "bg-neutral-800/20 border-neutral-700/30 text-neutral-400",
                                                        !isAvailable && "opacity-50 cursor-not-allowed"
                                                    )}
                                                >
                                                    <span className="text-[10px] font-bold uppercase">{labels[provider] || provider}</span>
                                                    {!isAvailable && <span className="text-[8px] text-red-500">Indisponível</span>}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>



                                <div className="grid grid-cols-2 gap-2">
                                    {/* Execution Threads */}
                                    <div className="space-y-1">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <label className="text-[10px] font-bold text-neutral-500 uppercase block">
                                                    Threads de Execução
                                                </label>
                                                <Tooltip content={helpTexts['execution_thread_count']}>
                                                    <Info size={12} className="text-neutral-500 cursor-help" />
                                                </Tooltip>
                                            </div>
                                            <span className="text-xs font-bold text-emerald-500">{settings.execution_thread_count || 4}</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="1"
                                            max={Math.floor((systemInfo?.cpu_count || navigator.hardwareConcurrency || 16) * 0.8)}
                                            step="1"
                                            value={settings.execution_thread_count || 4}
                                            onChange={(e) => handleChange("execution_thread_count", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                        />
                                        <div className="flex justify-between text-[10px] text-neutral-600 font-mono px-1">
                                            <span>1</span>
                                            <span>{Math.floor((systemInfo?.cpu_count || navigator.hardwareConcurrency || 16) * 0.8)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    {/* Memory Strategy */}
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Estratégia de Memória</label>
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
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase flex justify-between">
                                            Limite de Memória
                                            <span className="text-emerald-500">{settings.system_memory_limit || 0} GB</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0" max="128" step="4"
                                            value={settings.system_memory_limit || 0}
                                            onChange={(e) => handleChange("system_memory_limit", e.target.value)}
                                            className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                                        />
                                    </div>
                                </div>

                                <div className="pt-2 border-t border-neutral-800/50">
                                    {/* Log Level */}
                                    <div className="space-y-1">
                                        <label className="text-[10px] font-bold text-neutral-500 uppercase">Nível de Log</label>
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
                                </div>


                                <div className="pt-2 border-t border-neutral-800/50">
                                    <button
                                        onClick={() => handleChange("keep_temp", !settings.keep_temp)}
                                        className={cn(
                                            "w-full flex items-center justify-between p-2 rounded-lg border transition-all",
                                            settings.keep_temp
                                                ? "bg-emerald-600/10 border-emerald-500/50 text-emerald-500"
                                                : "bg-neutral-800 border-neutral-700 text-neutral-400"
                                        )}
                                    >
                                        <span className="text-xs font-bold uppercase">Manter Arquivos Temporários</span>
                                        <div className={cn("w-10 h-5 rounded-full relative transition-colors", settings.keep_temp ? "bg-emerald-600" : "bg-neutral-700")}>
                                            <div className={cn("absolute top-1 w-3 h-3 bg-white rounded-full transition-all", settings.keep_temp ? "left-6" : "left-1")} />
                                        </div>
                                    </button>
                                </div>

                                {/* Hard Debugging / Troubleshooting */}
                                <div className="space-y-2 pt-2 border-t border-neutral-800/50">
                                    <div className="flex items-center gap-2">
                                        <Bug size={14} className="text-neutral-500" />
                                        <label className="text-xs font-bold text-neutral-500 uppercase tracking-wider">
                                            Depuração Avançada
                                        </label>
                                    </div>
                                    <button
                                        onClick={() => handleChange("export_problem_frames", !settings.export_problem_frames)}
                                        className={cn(
                                            "w-full flex items-center justify-between p-2 rounded-lg border transition-all",
                                            settings.export_problem_frames
                                                ? "bg-emerald-600/10 border-emerald-500/30 shadow-[0_0_15px_rgba(37,99,235,0.1)]"
                                                : "bg-neutral-800/20 border-neutral-700/30 text-neutral-400"
                                        )}
                                    >
                                        <div className="flex flex-col items-start gap-1">
                                            <span className={cn("text-xs font-bold uppercase", settings.export_problem_frames ? "text-white" : "text-neutral-400")}>
                                                Exportar Quadros com Falha
                                            </span>
                                            <span className="text-[10px] opacity-60">Salva quadros onde rostos não foram encontrados em .assets/debug</span>
                                        </div>
                                        <div className={cn(
                                            "w-10 h-5 rounded-full relative transition-colors",
                                            settings.export_problem_frames ? "bg-emerald-500" : "bg-neutral-700"
                                        )}>
                                            <div className={cn(
                                                "absolute top-1 w-3 h-3 bg-white rounded-full transition-all",
                                                settings.export_problem_frames ? "left-6" : "left-1"
                                            )} />
                                        </div>
                                    </button>
                                </div>
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

            {/* Job Details Modal */}
            {selectedJobDetails && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-neutral-900 rounded-xl border border-neutral-700 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-neutral-700">
                            <div className="flex items-center gap-3">
                                <FileText size={20} className="text-emerald-500" />
                                <div>
                                    <h3 className="text-lg font-bold text-white">Detalhes da Tarefa</h3>
                                    <p className="text-xs font-mono text-neutral-400">{selectedJobDetails.id}</p>
                                </div>
                            </div>
                            <button
                                onClick={closeJobDetails}
                                className="p-2 hover:bg-neutral-800 rounded-lg transition-colors text-neutral-400 hover:text-white"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {/* Status & Info */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-neutral-800/50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-neutral-400 mb-1">
                                        <Info size={12} />
                                        <span className="text-[10px] uppercase font-bold">Status</span>
                                    </div>
                                    <span className={cn(
                                        "text-sm font-bold uppercase",
                                        selectedJobDetails.status === 'drafted' && "text-yellow-500",
                                        selectedJobDetails.status === 'queued' && "text-emerald-500",
                                        selectedJobDetails.status === 'completed' && "text-green-500",
                                        selectedJobDetails.status === 'failed' && "text-emerald-500",
                                    )}>
                                        {selectedJobDetails.status}
                                    </span>
                                </div>
                                <div className="bg-neutral-800/50 rounded-lg p-3">
                                    <div className="flex items-center gap-2 text-neutral-400 mb-1">
                                        <Clock size={12} />
                                        <span className="text-[10px] uppercase font-bold">Criado</span>
                                    </div>
                                    <span className="text-sm text-white">
                                        {selectedJobDetails.date_created ? new Date(selectedJobDetails.date_created).toLocaleString() : 'N/A'}
                                    </span>
                                </div>
                            </div>

                            {/* Steps */}
                            <div>
                                <div className="flex items-center gap-2 text-neutral-400 mb-2">
                                    <Cpu size={14} />
                                    <span className="text-xs uppercase font-bold">Passos ({selectedJobDetails.step_count})</span>
                                </div>
                                <div className="space-y-3">
                                    {selectedJobDetails.steps?.map((step: any, idx: number) => (
                                        <div key={idx} className="bg-neutral-800/50 rounded-lg p-3 border border-neutral-700">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs font-bold text-white">Passo {idx + 1}</span>
                                                <span className={cn(
                                                    "text-[9px] px-2 py-0.5 rounded font-bold uppercase",
                                                    step.status === 'completed' ? "bg-green-500/20 text-green-500" :
                                                        step.status === 'failed' ? "bg-emerald-500/20 text-emerald-500" :
                                                            "bg-neutral-700 text-neutral-400"
                                                )}>
                                                    {step.status}
                                                </span>
                                            </div>

                                            {/* Target & Output */}
                                            <div className="space-y-1 text-[10px]">
                                                {step.target_path && (
                                                    <div className="flex gap-2">
                                                        <span className="text-neutral-500 w-16">Alvo:</span>
                                                        <span className="text-neutral-300 truncate flex-1" title={step.target_path}>
                                                            {step.target_path.split('/').pop()}
                                                        </span>
                                                    </div>
                                                )}
                                                {step.output_path && (
                                                    <div className="flex gap-2">
                                                        <span className="text-neutral-500 w-16">Saída:</span>
                                                        <span className="text-neutral-300 truncate flex-1" title={step.output_path}>
                                                            {step.output_path.split('/').pop()}
                                                        </span>
                                                    </div>
                                                )}

                                                {/* Processors */}
                                                {step.processors?.length > 0 && (
                                                    <div className="flex gap-2 mt-2">
                                                        <span className="text-neutral-500 w-16">Processadores:</span>
                                                        <div className="flex flex-wrap gap-1">
                                                            {step.processors.map((p: string, i: number) => (
                                                                <span key={i} className="px-1.5 py-0.5 bg-emerald-600/20 text-emerald-400 rounded text-[9px]">
                                                                    {p}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Source Paths */}
                                                {step.source_paths?.length > 0 && (
                                                    <div className="flex gap-2 mt-1">
                                                        <span className="text-neutral-500 w-16">Origens:</span>
                                                        <span className="text-neutral-300">
                                                            {step.source_paths.length} arquivo(s)
                                                        </span>
                                                    </div>
                                                )}

                                                {/* Frame Range */}
                                                {(step.trim_frame_start !== null || step.trim_frame_end !== null) && (
                                                    <div className="flex gap-2 mt-1">
                                                        <span className="text-neutral-500 w-16">Quadros:</span>
                                                        <span className="text-neutral-300">
                                                            {step.trim_frame_start ?? 0} - {step.trim_frame_end ?? 'end'}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-neutral-700 flex justify-end">
                            <button
                                onClick={closeJobDetails}
                                className="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 rounded-lg text-sm font-bold transition-colors"
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
