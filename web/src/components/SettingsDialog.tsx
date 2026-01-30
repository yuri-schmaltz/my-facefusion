import { useState, useEffect } from "react";
import { config } from "@/services/api";
import { X, Save } from "lucide-react";
import { cn } from "@/lib/utils";

interface SettingsDialogProps {
    isOpen: boolean;
    onClose: () => void;
}

const FACE_MASK_TYPES = ['box', 'occlusion', 'area', 'region'];
const FACE_MASK_REGIONS = ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip'];
const OUTPUT_VIDEO_ENCODERS = ['libx264', 'libx264rgb', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo'];

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
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
        if (isOpen) {
            config.getSettings().then((res) => {
                setSettings((prev: any) => ({ ...prev, ...res.data }));
            });
        }
    }, [isOpen]);

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
            // execution_providers is already top level in our updated state management in api_server, but kept in settings bag for safety or removed from bag if direct
            // The api_server update_config handles top-level keys now, so we can just pass settings as is mostly.

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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl bg-neutral-900 border border-neutral-800 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-6 border-b border-neutral-800 shrink-0">
                    <h2 className="text-lg font-semibold text-white">Configurações</h2>
                    <button onClick={onClose} className="text-neutral-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 space-y-8 overflow-y-auto custom-scrollbar">
                    {/* Face Selector Mode */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Modo de Seleção de Rosto
                        </label>
                        <select
                            value={settings.face_selector_mode || "reference"}
                            onChange={(e) => handleChange("face_selector_mode", e.target.value)}
                            className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                        >
                            <option value="reference">Referência (Um Rosto)</option>
                            <option value="one">Único (Primeiro Encontrado)</option>
                            <option value="many">Muitos (Todos os Rostos)</option>
                        </select>
                    </div>

                    {/* Face Mask Types */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Tipos de Máscara Facial
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {FACE_MASK_TYPES.map((type) => (
                                <button
                                    key={type}
                                    onClick={() => toggleArrayItem("face_mask_types", type)}
                                    className={cn(
                                        "px-3 py-1.5 text-xs font-medium rounded-full border transition-all",
                                        (settings.face_mask_types || []).includes(type)
                                            ? "bg-emerald-600 border-emerald-500 text-white"
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
                            Regiões de Máscara Facial
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {FACE_MASK_REGIONS.map((region) => (
                                <button
                                    key={region}
                                    onClick={() => toggleArrayItem("face_mask_regions", region)}
                                    className={cn(
                                        "px-3 py-1.5 text-xs font-medium rounded-full border transition-all",
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Output Encoding */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-neutral-300 block">
                                Codificador de Vídeo
                            </label>
                            <select
                                value={settings.output_video_encoder || "libx264"}
                                onChange={(e) => handleChange("output_video_encoder", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                            >
                                {OUTPUT_VIDEO_ENCODERS.map(enc => (
                                    <option key={enc} value={enc}>{enc}</option>
                                ))}
                            </select>
                        </div>

                        {/* Video Quality */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-neutral-300 flex justify-between items-center">
                                <span>Qualidade de Saída</span>
                                <span className="text-emerald-500 font-bold">{settings.output_video_quality || 80}%</span>
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={settings.output_video_quality || 80}
                                onChange={(e) => handleChange("output_video_quality", e.target.value)}
                                className="w-full h-2 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Execution Threads */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-neutral-300 block">
                                Threads de Execução
                            </label>
                            <input
                                type="number"
                                min="1"
                                max="128"
                                value={settings.execution_thread_count || 4}
                                onChange={(e) => handleChange("execution_thread_count", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                            />
                        </div>

                        {/* Execution Queue */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-neutral-300 block">
                                Fila de Execução
                            </label>
                            <input
                                type="number"
                                min="1"
                                max="32"
                                value={settings.execution_queue_count || 1}
                                onChange={(e) => handleChange("execution_queue_count", e.target.value)}
                                className="w-full bg-neutral-800 border-neutral-700 text-white rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                            />
                        </div>
                    </div>

                    {/* Execution Provider */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-neutral-300 block">
                            Provedor de Execução
                        </label>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            {["cuda", "cpu", "openvino", "rocm"].map((provider) => {
                                const current = settings.execution_providers || [];
                                const isSelected = current.includes(provider);

                                return (
                                    <button
                                        key={provider}
                                        onClick={() => {
                                            // Toggle provider logic for array
                                            toggleArrayItem("execution_providers", provider);
                                        }}
                                        className={cn(
                                            "px-3 py-2 text-sm font-medium rounded-lg border text-center transition-all",
                                            isSelected
                                                ? "bg-emerald-600/20 border-emerald-500 text-emerald-500"
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

                <div className="p-6 border-t border-neutral-800 flex justify-end shrink-0 bg-neutral-900">
                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="px-6 py-2.5 bg-white text-black font-bold rounded-lg hover:bg-neutral-200 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? <span className="animate-spin">⏳</span> : <Save size={18} />}
                        Salvar Alterações
                    </button>
                </div>
            </div>
        </div>
    );
}
