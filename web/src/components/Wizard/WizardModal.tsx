import React, { useState, useEffect, useRef } from "react";
import { X, ChevronRight, Wand2, Search, Users, Settings, Loader2, Target, HardDrive, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { wizard } from "@/services/api";

interface WizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    targetPath: string;
}

type Step = 'analyze' | 'cluster' | 'optimize' | 'generate';

export const WizardModal: React.FC<WizardModalProps> = ({ isOpen, onClose, targetPath }) => {
    const [currentStep, setCurrentStep] = useState<Step>('analyze');
    const [status, setStatus] = useState<string>('idle'); // 'idle', 'loading', 'completed', 'failed'
    const [jobId, setJobId] = useState<string | null>(null);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [clusters, setClusters] = useState<any[]>([]);
    const [suggestions, setSuggestions] = useState<any>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStatus, setCurrentStatus] = useState("queued");
    const [statusMessage, setStatusMessage] = useState("Initializing...");

    const pollInterval = useRef<any>(null);

    const statusLabels: Record<string, string> = {
        'detecting_scenes': 'Detecting scenes...',
        'analyzing_faces': 'Analyzing faces in scenes...',
        'completed': 'Analysis complete!',
        'failed': 'Analysis failed.',
        'queued': 'Waiting in queue...'
    };

    // Cleanup on unmount or when closed
    useEffect(() => {
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current);
        };
    }, []);

    // Initial Trigger
    useEffect(() => {
        if (isOpen && currentStep === 'analyze' && !jobId && status === 'idle') {
            startAnalysis();
        } else if (!isOpen) {
            // Stop polling if closed
            if (pollInterval.current) clearInterval(pollInterval.current);
        }
    }, [isOpen]);

    const startAnalysis = async () => {
        if (!targetPath) {
            setStatus('failed');
            alert("No target video selected. Please select a video to analyze.");
            onClose();
            return;
        }
        setStatus('loading');
        setProgress(0);
        setCurrentStatus("queued");
        setStatusMessage("Initializing...");

        // Clear any existing interval
        if (pollInterval.current) clearInterval(pollInterval.current);

        try {
            const res = await wizard.analyze(targetPath);
            const id = res.data.job_id;
            setJobId(id);

            // Poll for progress
            pollInterval.current = setInterval(async () => {
                try {
                    const pRes = await wizard.getProgress(id);
                    const { status: jobStatus, progress: p, result, error } = pRes.data;

                    setProgress(p);
                    setCurrentStatus(jobStatus);
                    setStatusMessage(statusLabels[jobStatus] || jobStatus);

                    if (jobStatus === 'completed') {
                        if (pollInterval.current) clearInterval(pollInterval.current);
                        setAnalysisResult(result);
                        setStatus('completed');
                        setCurrentStep('cluster');
                        fetchClusters(id);
                    } else if (jobStatus === 'failed') {
                        if (pollInterval.current) clearInterval(pollInterval.current);
                        setStatus('failed');
                        alert("Analysis failed: " + error);
                    }
                } catch (err) {
                    console.error("Polling failed", err);
                    if (pollInterval.current) clearInterval(pollInterval.current);
                    setStatus('failed');
                }
            }, 1000);
        } catch (err) {
            console.error("Analysis failed", err);
            setStatus('failed');
        }
    };

    const fetchClusters = async (id: string) => {
        setStatus('loading');
        try {
            const res = await wizard.cluster(id);
            setClusters(res.data.clusters);
            setStatus('completed');
        } catch (err) {
            console.error("Clustering failed", err);
            setStatus('failed');
        }
    };

    const runOptimization = async () => {
        if (!jobId) return;
        setStatus('loading');
        try {
            const res = await wizard.suggest(jobId);
            setSuggestions(res.data.suggestions);
            setCurrentStep('optimize');
            setStatus('completed');
        } catch (err) {
            console.error("Suggestions failed", err);
            setStatus('failed');
        }
    };

    const handleGenerateJobs = async () => {
        if (!jobId) return;
        setIsGenerating(true);
        try {
            await wizard.generate(jobId);
            onClose();
        } catch (err) {
            console.error("Failed to generate jobs", err);
        } finally {
            setIsGenerating(false);
        }
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
                        { id: 'generate', label: 'Generation', icon: Wand2 },
                    ].map((step) => (
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
                        <div className="h-full flex flex-col items-center justify-center space-y-8 py-10">
                            <div className="relative">
                                <Loader2 size={64} className="text-red-600 animate-spin" />
                            </div>
                            <div className="text-center space-y-4 w-full max-w-md">
                                <h3 className="text-lg font-bold text-white mb-2">{statusMessage}</h3>
                                <div className="flex items-center justify-center gap-3 text-sm text-neutral-400">
                                    <div className={cn("px-2 py-0.5 rounded border transition-colors", currentStatus === 'detecting_scenes' ? "border-red-500/50 bg-red-500/10 text-red-500" : "border-neutral-800 bg-neutral-900")}>
                                        Scenes
                                    </div>
                                    <ChevronRight size={14} className="text-neutral-700" />
                                    <div className={cn("px-2 py-0.5 rounded border transition-colors", currentStatus === 'analyzing_faces' ? "border-red-500/50 bg-red-500/10 text-red-500" : "border-neutral-800 bg-neutral-900")}>
                                        Faces
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-neutral-500">
                                        <span>Progress</span>
                                        <span>{Math.round(progress * 100)}%</span>
                                    </div>
                                    <div className="h-2 w-full bg-neutral-800 rounded-full overflow-hidden border border-neutral-700/50 shadow-inner">
                                        <div
                                            className="h-full bg-red-600 transition-all duration-300 ease-out shadow-[0_0_10px_rgba(220,38,38,0.5)]"
                                            style={{ width: `${progress * 100}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {currentStep === 'cluster' && (
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-bold text-white">Detected Face Groups</h3>
                                <span className="text-xs font-mono text-neutral-500 uppercase tracking-widest">{clusters.length} Unique Faces Found</span>
                            </div>

                            {status === 'loading' ? (
                                <div className="flex items-center justify-center py-20">
                                    <Loader2 className="animate-spin text-red-600" size={32} />
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                    {clusters.map((cluster, idx) => (
                                        <div key={idx} className="bg-neutral-800/50 border border-neutral-700/50 rounded-xl p-4 hover:border-red-500/50 transition-all group">
                                            <div className="flex items-center gap-4">
                                                <div className="w-16 h-16 bg-neutral-700 rounded-lg flex items-center justify-center text-neutral-500 overflow-hidden">
                                                    {cluster.thumbnail ? (
                                                        <img
                                                            src={cluster.thumbnail}
                                                            alt={`Face Group ${idx + 1}`}
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <Users size={24} />
                                                    )}
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

                    {currentStep === 'optimize' && suggestions && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
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

                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-neutral-800/50 p-4 rounded-xl border border-neutral-700">
                                    <h4 className="text-sm font-bold text-neutral-300 mb-2 flex items-center gap-2">
                                        <Target size={14} className="text-blue-400" /> Face Detector
                                    </h4>
                                    <div className="space-y-1">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Model</span>
                                            <span className="text-white font-mono">{suggestions.face_detector_model}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Size</span>
                                            <span className="text-white font-mono">{suggestions.face_detector_size}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Score</span>
                                            <span className="text-white font-mono">{suggestions.face_detector_score}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-neutral-800/50 p-4 rounded-xl border border-neutral-700">
                                    <h4 className="text-sm font-bold text-neutral-300 mb-2 flex items-center gap-2">
                                        <HardDrive size={14} className="text-green-400" /> System Resources
                                    </h4>
                                    <div className="space-y-1">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Memory Limit</span>
                                            <span className="text-white font-mono">{suggestions.system_memory_limit} GB</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Execution Threads</span>
                                            <span className="text-white font-mono">{suggestions.execution_thread_count}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl flex items-start gap-3">
                                <Info className="text-blue-400 shrink-0 mt-0.5" size={16} />
                                <p className="text-xs text-blue-200">
                                    These settings have been optimized based on the resolution of your video and your available system memory.
                                </p>
                            </div>
                        </div>
                    )}

                    {currentStep === 'generate' && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 text-center py-10">
                            <div className="flex justify-center">
                                <div className="p-4 bg-green-500/10 rounded-full mb-4">
                                    <Wand2 size={48} className="text-green-500" />
                                </div>
                            </div>
                            <h3 className="text-2xl font-bold text-white">Ready to Generate</h3>
                            <p className="text-neutral-400 max-w-md mx-auto">
                                We will create <strong>{clusters.length} usage jobs</strong> based on the scenes and face groups we identified.
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
                                <div className="bg-neutral-800 p-4 rounded-xl border border-neutral-700">
                                    <span className="block text-xs text-neutral-500 uppercase font-bold mb-1">Scenes</span>
                                    <span className="text-xl font-mono text-white">{Object.keys(analysisResult?.scenes || {}).length}</span>
                                </div>
                                <div className="bg-neutral-800 p-4 rounded-xl border border-neutral-700">
                                    <span className="block text-xs text-neutral-500 uppercase font-bold mb-1">Face Groups</span>
                                    <span className="text-xl font-mono text-white">{clusters.length}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer / Actions */}
                <div className="p-6 border-t border-neutral-800 flex justify-between bg-neutral-950/50">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 rounded-xl text-neutral-400 hover:bg-neutral-800 transition-colors font-medium text-sm"
                    >
                        Cancel
                    </button>

                    {currentStep === 'cluster' && (
                        <button
                            onClick={runOptimization}
                            disabled={status === 'loading'}
                            className="bg-white text-black px-6 py-2 rounded-xl font-bold hover:bg-neutral-200 transition-colors flex items-center gap-2"
                        >
                            {status === 'loading' && <Loader2 size={16} className="animate-spin" />}
                            Next: Optimization
                        </button>
                    )}

                    {currentStep === 'optimize' && (
                        <button
                            onClick={() => setCurrentStep('generate')}
                            className="bg-red-600 text-white px-6 py-2 rounded-xl font-bold hover:bg-red-500 transition-colors flex items-center gap-2"
                        >
                            Next: Generation
                        </button>
                    )}

                    {currentStep === 'generate' && (
                        <button
                            onClick={handleGenerateJobs}
                            disabled={isGenerating}
                            className="bg-red-600 text-white px-6 py-2 rounded-xl font-bold hover:bg-red-500 transition-colors flex items-center gap-2"
                        >
                            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
                            Generate Jobs
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
