import React, { useState, useEffect } from "react";
import { X, ChevronRight, ChevronLeft, Check, Wand2, Search, Users, Settings, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { wizard, config } from "@/services/api";

interface WizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    targetPath: string;
}

type Step = 'analyze' | 'cluster' | 'optimize';

export const WizardModal: React.FC<WizardModalProps> = ({ isOpen, onClose, targetPath }) => {
    const [currentStep, setCurrentStep] = useState<Step>('analyze');
    const [loading, setLoading] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [clusters, setClusters] = useState<any[]>([]);
    const [suggestions, setSuggestions] = useState<any>(null);

    useEffect(() => {
        if (isOpen && targetPath) {
            startAnalysis();
        }
    }, [isOpen, targetPath]);

    const startAnalysis = async () => {
        setLoading(true);
        try {
            const res = await wizard.analyze(targetPath);
            setJobId(res.data.job_id);
            setAnalysisResult(res.data);
            setCurrentStep('cluster');
            fetchClusters(res.data.job_id);
        } catch (err) {
            console.error("Analysis failed", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchClusters = async (id: string) => {
        setLoading(true);
        try {
            const res = await wizard.cluster(id);
            setClusters(res.data.clusters);
        } catch (err) {
            console.error("Clustering failed", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchSuggestions = async () => {
        if (!jobId) return;
        setLoading(true);
        try {
            const res = await wizard.suggest(jobId);
            setSuggestions(res.data.suggestions);
            setCurrentStep('optimize');
        } catch (err) {
            console.error("Suggestions failed", err);
        } finally {
            setLoading(false);
        }
    };

    const handleApply = async () => {
        if (suggestions) {
            await config.update(suggestions);
        }
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
            <div className="w-full max-w-4xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="p-6 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-red-600 rounded-lg">
                            <Wand2 size={20} className="text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Automatic Wizard</h2>
                            <p className="text-xs text-neutral-500">Smart scene detection and face grouping</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-neutral-800 rounded-full transition-colors text-neutral-400">
                        <X size={20} />
                    </button>
                </div>

                {/* Progress Bar */}
                <div className="flex border-b border-neutral-800">
                    {[
                        { id: 'analyze', label: 'Analysis', icon: Search },
                        { id: 'cluster', label: 'Grouping', icon: Users },
                        { id: 'optimize', label: 'Optimization', icon: Settings },
                    ].map((step, idx) => (
                        <div
                            key={step.id}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 py-3 text-sm font-bold border-b-2 transition-all",
                                currentStep === step.id
                                    ? "border-red-600 text-white bg-red-600/5"
                                    : "border-transparent text-neutral-500"
                            )}
                        >
                            <step.icon size={16} />
                            {step.label}
                        </div>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {currentStep === 'analyze' && (
                        <div className="h-full flex flex-col items-center justify-center space-y-6">
                            <div className="relative">
                                <Search size={64} className="text-red-600 animate-pulse" />
                                <div className="absolute inset-0 border-2 border-red-600 rounded-full animate-ping opacity-20" />
                            </div>
                            <div className="text-center">
                                <h3 className="text-lg font-bold text-white mb-2">Analyzing Video...</h3>
                                <p className="text-sm text-neutral-400 max-w-sm">
                                    Detecting scenes and identifying unique face characteristics to optimize your workflow.
                                </p>
                            </div>
                        </div>
                    )}

                    {currentStep === 'cluster' && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-bold text-white">Detected Face Groups</h3>
                                <span className="text-xs font-mono text-neutral-500 uppercase tracking-widest">{clusters.length} Unique Faces Found</span>
                            </div>

                            {loading ? (
                                <div className="flex items-center justify-center py-20">
                                    <Loader2 className="animate-spin text-red-600" size={32} />
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                    {clusters.map((cluster, idx) => (
                                        <div key={idx} className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 hover:border-red-500/50 transition-all group">
                                            <div className="flex items-center gap-4">
                                                <div className="w-16 h-16 bg-neutral-700 rounded-lg flex items-center justify-center text-neutral-500 overflow-hidden">
                                                    {/* Placeholder for crop thumbnail */}
                                                    <Users size={24} />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-white">Face Group #{idx + 1}</p>
                                                    <p className="text-[10px] text-neutral-500 uppercase font-mono">{cluster.face_count} Appearances</p>
                                                    <div className="flex gap-1 mt-1">
                                                        <span className="px-1.5 py-0.5 bg-neutral-900 rounded text-[9px] text-neutral-400 capitalize">{cluster.representative.gender}</span>
                                                        <span className="px-1.5 py-0.5 bg-neutral-900 rounded text-[9px] text-neutral-400">{cluster.representative.age}y</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {currentStep === 'optimize' && (
                        <div className="space-y-8">
                            <div className="bg-red-600/10 border border-red-600/20 rounded-xl p-6 flex items-start gap-4">
                                <Settings className="text-red-500 shrink-0" size={24} />
                                <div>
                                    <h4 className="font-bold text-white mb-1">Recommended Optimization</h4>
                                    <p className="text-sm text-neutral-400 leading-relaxed">
                                        Our smart logic analyzed your system and the video content. We've selected models and thread configurations that balance quality and speed.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-600 uppercase tracking-tighter">Recommended Processor</label>
                                    <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                                        <p className="text-sm font-bold text-white">{suggestions?.face_swapper_model || 'Standard'}</p>
                                        <p className="text-[10px] text-neutral-500">Optimized for detected face resolution</p>
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold text-neutral-600 uppercase tracking-tighter">Enhancement Strategy</label>
                                    <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                                        <p className="text-sm font-bold text-white">{suggestions?.face_enhancer_model || 'Enabled'}</p>
                                        <p className="text-[10px] text-neutral-500">Based on scene lighting/compression</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-neutral-800 flex items-center justify-between bg-neutral-950/30">
                    <div>
                        {currentStep !== 'analyze' && (
                            <button
                                onClick={() => currentStep === 'cluster' ? setCurrentStep('analyze') : setCurrentStep('cluster')}
                                className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors text-sm font-bold"
                            >
                                <ChevronLeft size={16} />
                                Back
                            </button>
                        )}
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-6 py-2.5 rounded-xl border border-neutral-700 text-neutral-400 hover:bg-neutral-800 transition-all text-sm font-bold"
                        >
                            Cancel
                        </button>

                        {currentStep === 'cluster' && (
                            <button
                                onClick={fetchSuggestions}
                                disabled={loading}
                                className="px-8 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl shadow-lg shadow-red-600/20 transition-all text-sm font-bold flex items-center gap-2 disabled:opacity-50"
                            >
                                Next Step
                                <ChevronRight size={16} />
                            </button>
                        )}

                        {currentStep === 'optimize' && (
                            <button
                                onClick={handleApply}
                                className="px-8 py-2.5 bg-white hover:bg-neutral-200 text-black rounded-xl shadow-lg transition-all text-sm font-bold flex items-center gap-2"
                            >
                                <Check size={16} />
                                Apply Optimizations
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
