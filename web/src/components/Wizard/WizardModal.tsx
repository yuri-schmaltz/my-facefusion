import React, { useState, useEffect, useRef } from "react";
import { X, ChevronRight, Wand2, Search, Users, Settings, Loader2, Target, HardDrive, Info, Check, Square, CheckSquare, Merge, Upload, ArrowRight, UserPlus } from "lucide-react";
import { cn } from "@/lib/utils";
import { wizard } from "@/services/api";

interface WizardModalProps {
    isOpen: boolean;
    onClose: () => void;
    targetPath: string;
}

type Step = 'source' | 'analyze' | 'cluster' | 'optimize' | 'generate';

export const WizardModal: React.FC<WizardModalProps> = ({ isOpen, onClose, targetPath }) => {
    const [currentStep, setCurrentStep] = useState<Step>('source');
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
    const [isRefining, setIsRefining] = useState(false);

    // New state for manual refinement
    const [selectedClusters, setSelectedClusters] = useState<Set<number>>(new Set());
    const [isMerging, setIsMerging] = useState(false);
    const [sourceFiles, setSourceFiles] = useState<File[]>([]); // For the new 'source' step
    const [sourcePaths, setSourcePaths] = useState<string[]>([]);
    const [activeSourceIndex, setActiveSourceIndex] = useState<number | null>(null);
    const [clusterAssignments, setClusterAssignments] = useState<Record<number, number>>({}); // clusterIdx -> sourceIdx

    const handleClusterClick = (idx: number) => {
        if (activeSourceIndex !== null) {
            // Assignment Mode: Assign active source to this cluster
            setClusterAssignments(prev => {
                const newAssignments = { ...prev };
                // Toggle: if already assigned to this source, unassign
                if (newAssignments[idx] === activeSourceIndex) {
                    delete newAssignments[idx];
                } else {
                    newAssignments[idx] = activeSourceIndex;
                }
                return newAssignments;
            });
        } else {
            // Selection Mode: Toggle selection
            toggleClusterSelection(idx);
        }
    };

    const toggleClusterSelection = (idx: number) => {
        const newSelected = new Set(selectedClusters);
        if (newSelected.has(idx)) {
            newSelected.delete(idx);
        } else {
            newSelected.add(idx);
        }
        setSelectedClusters(newSelected);
    };

    const handleMergeSelected = async () => {
        if (!jobId || selectedClusters.size < 2) return;
        setIsMerging(true);
        try {
            const indices = Array.from(selectedClusters);
            const res = await wizard.mergeClusters(jobId, indices);
            setClusters(res.data.clusters);
            setSelectedClusters(new Set()); // Clear selection after merge
        } catch (err) {
            console.error("Merge failed", err);
            // Optional: show toast error
        } finally {
            setIsMerging(false);
        }
    };


    const handleRefineGroups = async () => {
        if (!jobId) return;
        setIsRefining(true);
        setStatus('loading');
        try {
            // Call cluster endpoint again with refine=true
            const res = await wizard.cluster(jobId, true);
            setClusters(res.data.clusters);
            setStatus('completed');
        } catch (err) {
            console.error("Refinement failed", err);
            setStatus('failed');
        } finally {
            setIsRefining(false);
        }
    };

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

    // Stop polling when modal closes
    useEffect(() => {
        if (!isOpen) {
            if (pollInterval.current) clearInterval(pollInterval.current);
        }
    }, [isOpen]);

    // Step navigation logic - determines which steps are accessible
    const canNavigateToStep = (stepId: Step): boolean => {
        const stepOrder: Step[] = ['source', 'analyze', 'cluster', 'optimize', 'generate'];
        const currentIndex = stepOrder.indexOf(currentStep);
        const targetIndex = stepOrder.indexOf(stepId);

        // Can always go back
        if (targetIndex < currentIndex) return true;

        // Can only go forward if current step is completed
        if (stepId === 'cluster' && status === 'completed' && analysisResult) return true;
        if (stepId === 'optimize' && clusters.length > 0) return true;
        if (stepId === 'generate' && suggestions) return true;

        return false;
    };

    const handleStepClick = (stepId: Step) => {
        if (canNavigateToStep(stepId) || stepId === currentStep) {
            setCurrentStep(stepId);
        }
    };

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

            // Upload Sources
            if (sourceFiles.length > 0) {
                setStatusMessage("Uploading source files...");
                const paths: string[] = [];
                for (const file of sourceFiles) {
                    try {
                        const upRes = await wizard.uploadSource(id, file);
                        paths.push(upRes.data.path);
                    } catch (uploadErr) {
                        console.error("Failed to upload source", file.name, uploadErr);
                    }
                }
                setSourcePaths(paths);
            }

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

        // Save Assignments
        if (Object.keys(clusterAssignments).length > 0) {
            const mappedAssignments: Record<number, string> = {};
            for (const [clusterIdx, sourceIdx] of Object.entries(clusterAssignments)) {
                // Ensure sourcePath exists for this index
                if (sourcePaths[Number(sourceIdx)]) {
                    mappedAssignments[Number(clusterIdx)] = sourcePaths[Number(sourceIdx)];
                }
            }

            if (Object.keys(mappedAssignments).length > 0) {
                try {
                    await wizard.assignSources(jobId, mappedAssignments);
                } catch (e) {
                    console.error("Failed to save assignments", e);
                }
            }
        }

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
            const result = await wizard.generate(jobId);
            const count = result?.count || 0;
            alert(`✅ ${count} job(s) created successfully!\n\nCheck the Jobs panel to manage and run them.`);
            onClose();
        } catch (err) {
            console.error("Failed to generate jobs", err);
            alert("❌ Failed to generate jobs. Check the console for details.");
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
                        <div className="p-4 bg-red-600/10 rounded-full inline-block">
                            <Wand2 size={20} className="text-red-500" />
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

                {/* Progress Bar - Clickable Steps */}
                <div className="flex border-b border-neutral-800">
                    {[
                        { id: 'analyze' as Step, label: 'Analysis', icon: Search },
                        { id: 'cluster' as Step, label: 'Grouping', icon: Users },
                        { id: 'optimize' as Step, label: 'Optimization', icon: Settings },
                        { id: 'generate' as Step, label: 'Generation', icon: Wand2 },
                    ].map((step) => {
                        const isClickable = canNavigateToStep(step.id) || step.id === currentStep;
                        return (
                            <button
                                key={step.id}
                                onClick={() => handleStepClick(step.id)}
                                disabled={!isClickable}
                                className={cn(
                                    "flex-1 flex items-center justify-center gap-2 py-3 text-sm font-bold border-b-2 transition-all",
                                    currentStep === step.id
                                        ? "border-red-600 text-white bg-red-600/5"
                                        : isClickable
                                            ? "border-transparent text-neutral-400 hover:text-white hover:bg-neutral-800/50 cursor-pointer"
                                            : "border-transparent text-neutral-600 cursor-not-allowed"
                                )}
                            >
                                <step.icon size={16} />
                                {step.label}
                            </button>
                        );
                    })}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {currentStep === 'analyze' && (
                        <div className="h-full flex flex-col items-center justify-center space-y-8 py-10">
                            {status === 'idle' ? (
                                /* Start Analysis View */
                                <>
                                    <div className="text-center space-y-4">
                                        <div className="p-4 bg-red-600/10 rounded-full inline-block">
                                            <Search size={48} className="text-red-500" />
                                        </div>
                                        <h3 className="text-xl font-bold text-white">Ready to Analyze</h3>
                                        <p className="text-neutral-400 max-w-md">
                                            The wizard will detect scenes and analyze faces in your video to create optimized processing jobs.
                                        </p>
                                        <div className="text-xs text-neutral-500 bg-neutral-800/50 rounded-lg p-3 max-w-md">
                                            <strong>Target:</strong> {targetPath.split('/').pop() || targetPath}
                                        </div>
                                    </div>
                                    <button
                                        onClick={startAnalysis}
                                        className="px-8 py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg transition-all flex items-center gap-2 shadow-lg shadow-red-600/20"
                                    >
                                        <Wand2 size={18} />
                                        Start Analysis
                                    </button>
                                </>
                            ) : status === 'loading' ? (
                                /* Loading View */
                                <>
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
                                </>
                            ) : status === 'completed' ? (
                                /* Completed View */
                                <div className="text-center space-y-4">
                                    <div className="p-4 bg-green-600/10 rounded-full inline-block">
                                        <Search size={48} className="text-green-500" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white">Analysis Complete!</h3>
                                    <p className="text-neutral-400">
                                        Found {analysisResult?.scenes?.length || 0} scenes with faces detected.
                                    </p>
                                    <button
                                        onClick={() => setCurrentStep('cluster')}
                                        className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg transition-all flex items-center gap-2 mx-auto"
                                    >
                                        Continue to Grouping
                                        <ChevronRight size={16} />
                                    </button>
                                </div>
                            ) : (
                                /* Failed View */
                                <div className="text-center space-y-4">
                                    <div className="p-4 bg-red-600/10 rounded-full inline-block">
                                        <X size={48} className="text-red-500" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white">Analysis Failed</h3>
                                    <p className="text-neutral-400">
                                        Something went wrong during the analysis.
                                    </p>
                                    <button
                                        onClick={() => { setStatus('idle'); setJobId(null); }}
                                        className="px-6 py-2 bg-neutral-700 hover:bg-neutral-600 text-white font-bold rounded-lg transition-all"
                                    >
                                        Try Again
                                    </button>
                                </div>
                            )}
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
                                <>
                                    {sourceFiles.length > 0 && (
                                        <div className="mb-6 p-4 bg-neutral-900/50 border border-neutral-800 rounded-xl">
                                            <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">Assign Sources</h4>
                                            <div className="flex gap-4 overflow-x-auto pb-2">
                                                <button
                                                    onClick={() => setActiveSourceIndex(null)}
                                                    className={cn(
                                                        "px-4 py-2 rounded-lg border text-sm font-medium transition-all whitespace-nowrap",
                                                        activeSourceIndex === null
                                                            ? "bg-blue-600 border-blue-500 text-white"
                                                            : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:text-white"
                                                    )}
                                                >
                                                    Select Mode
                                                </button>
                                                {sourceFiles.map((file, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => setActiveSourceIndex(i)}
                                                        className={cn(
                                                            "relative w-12 h-12 rounded-lg overflow-hidden border-2 transition-all p-0.5",
                                                            activeSourceIndex === i
                                                                ? "border-blue-500 ring-2 ring-blue-500/50"
                                                                : "border-neutral-700 opacity-70 hover:opacity-100"
                                                        )}
                                                    >
                                                        <img src={URL.createObjectURL(file)} className="w-full h-full object-cover rounded-md" />
                                                        {/* Count how many assigned */}
                                                        {Object.values(clusterAssignments).filter(idx => idx === i).length > 0 && (
                                                            <div className="absolute top-0 right-0 bg-blue-600 text-white text-[9px] w-4 h-4 flex items-center justify-center rounded-bl-md">
                                                                {Object.values(clusterAssignments).filter(idx => idx === i).length}
                                                            </div>
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                            <p className="text-[10px] text-neutral-500 mt-2">
                                                {activeSourceIndex !== null
                                                    ? "Click on a Face Group to assign this source face."
                                                    : "Click to select groups for merging."}
                                            </p>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pb-20">
                                        {clusters.map((cluster, idx) => (
                                            <div
                                                key={idx}
                                                onClick={() => handleClusterClick(idx)}
                                                className={cn(
                                                    "bg-neutral-800/50 border rounded-xl p-4 transition-all group cursor-pointer relative",
                                                    selectedClusters.has(idx) ? "border-blue-500 bg-blue-500/10" : "border-neutral-700/50 hover:border-blue-500/50",
                                                    clusterAssignments[idx] !== undefined ? "ring-1 ring-green-500/50" : ""
                                                )}
                                            >
                                                {/* Selection Indicator */}
                                                {activeSourceIndex === null && (
                                                    <div className="absolute top-3 right-3 text-blue-500 transition-opacity z-10">
                                                        {selectedClusters.has(idx) ? <CheckSquare size={20} /> : <Square size={20} className="text-neutral-600 opacity-0 group-hover:opacity-100" />}
                                                    </div>
                                                )}

                                                {/* Assignment Indicator */}
                                                {clusterAssignments[idx] !== undefined && sourceFiles[clusterAssignments[idx]] && (
                                                    <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full border-2 border-green-500 overflow-hidden z-20 shadow-lg bg-neutral-900">
                                                        <img src={URL.createObjectURL(sourceFiles[clusterAssignments[idx]])} className="w-full h-full object-cover" />
                                                    </div>
                                                )}

                                                <div className="flex items-center gap-4 pointer-events-none">
                                                    <div className="w-16 h-16 bg-neutral-700 rounded-lg flex items-center justify-center text-neutral-500 overflow-hidden shrink-0">
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
                                                    <div className="min-w-0">
                                                        <p className="text-sm font-bold text-white truncate">Face Group #{idx + 1}</p>
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
                                </>
                            )}

                            {/* Floating Action Bar for Merge */}
                            {selectedClusters.size > 1 && (
                                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
                                    <button
                                        onClick={handleMergeSelected}
                                        disabled={isMerging}
                                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-full shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed animate-in fade-in slide-in-from-bottom-4"
                                    >
                                        {isMerging ? (
                                            <Loader2 size={18} className="animate-spin" />
                                        ) : (
                                            <Merge size={18} />
                                        )}
                                        Merge {selectedClusters.size} Groups
                                    </button>
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
                                <div className="bg-neutral-800/50 p-4 rounded-xl border border-neutral-700 relative group">
                                    <h4 className="text-sm font-bold text-neutral-300 mb-2 flex items-center gap-2">
                                        <Target size={14} className="text-blue-400" /> Face Detector
                                        <div className="relative ml-auto">
                                            <Info size={12} className="text-neutral-600 cursor-help" />
                                            {/* Tooltip */}
                                            <div className="absolute right-0 top-6 w-48 p-2 bg-neutral-900 border border-neutral-700 rounded-lg shadow-xl text-[10px] text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                                                These settings control how faces are detected in the initial analysis phase. Models like 'yoloface' are faster, while 'retinaface' is more accurate.
                                            </div>
                                        </div>
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
                                            <span className="text-neutral-500">Providers</span>
                                            <span className="text-white font-mono text-right max-w-[100px] truncate" title={suggestions.execution_providers?.join(', ')}>
                                                {suggestions.execution_providers?.map((p: string) =>
                                                    p === 'cuda' ? 'NVIDIA GPU' :
                                                        p === 'coreml' ? 'Apple Neural' :
                                                            p === 'rocm' ? 'AMD GPU' :
                                                                p.toUpperCase()
                                                ).join(', ') || 'CPU'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-neutral-500">Memory Limit</span>
                                            <span className="text-white font-mono">{suggestions.system_memory_limit > 0 ? `${suggestions.system_memory_limit} GB` : 'Auto'}</span>
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
                        <div className="flex gap-2">
                            <button
                                onClick={handleRefineGroups}
                                disabled={status === 'loading' || isRefining}
                                className="bg-neutral-800 text-white px-4 py-2 rounded-xl border border-neutral-700 hover:bg-neutral-700 transition-colors flex items-center gap-2 text-sm"
                            >
                                {isRefining ? <Loader2 size={14} className="animate-spin" /> : <Users size={14} />}
                                Refine Groups
                            </button>
                            <button
                                onClick={runOptimization}
                                disabled={status === 'loading'}
                                className="bg-white text-black px-6 py-2 rounded-xl font-bold hover:bg-neutral-200 transition-colors flex items-center gap-2"
                            >
                                {status === 'loading' && <Loader2 size={16} className="animate-spin" />}
                                Next: Optimization
                            </button>
                        </div>
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
        </div >
    );
};
