
import { useState, useEffect } from "react";
import { files, execute, system, config } from "@/services/api";
import { Upload, Play, Loader2, Replace, Sparkles, AppWindow, Bug, Smile, Clock, Eraser, Palette, Mic2, Box, X, User, Film } from "lucide-react";
import { SettingsPanel } from "@/components/SettingsPanel";
import { cn } from "@/lib/utils";
import { Terminal, TerminalButton } from "@/components/Terminal";
import { Tooltip } from "@/components/ui/Tooltip";
import ProcessorSettings from "@/components/ProcessorSettings";
import FaceSelector from "@/components/FaceSelector";
import { MediaPreview } from "@/components/MediaPreview";
import { useJob } from "@/hooks/useJob";
// ... imports

// ... inside App component



const isVideo = (path: string) => {
  return path.match(/\.(mp4|webm|ogg|mov)$/i);
};

function App() {
  console.log("App Rendering...");
  const [processors, setProcessors] = useState<string[]>([]);
  const [activeMediaTab, setActiveMediaTab] = useState<'source' | 'target'>('target');
  const [activeProcessorTab, setActiveProcessorTab] = useState("face");
  const [activeProcessors, setActiveProcessors] = useState<string[]>([]);
  const [allSettings, setAllSettings] = useState<any>({});
  const [systemInfo, setSystemInfo] = useState<any>({ execution_providers: ['cpu'] });
  const [helpTexts, setHelpTexts] = useState<Record<string, string>>({});

  // App State
  const [sourcePath, setSourcePath] = useState<string | null>(null);
  const [targetPath, setTargetPath] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [lastSourceDir, setLastSourceDir] = useState<string>(() => localStorage.getItem("lastSourceDir") || "");
  const [lastTargetDir, setLastTargetDir] = useState<string>(() => localStorage.getItem("lastTargetDir") || "");
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0);
  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [previewResolution, setPreviewResolution] = useState("512x512");
  const [globalChoices, setGlobalChoices] = useState<any>({});

  useEffect(() => {
    config.getProcessors().then((res) => {
      setProcessors(res.data.available);
      setActiveProcessors(res.data.active || []);
    });
    config.getSettings().then((res) => {
      setAllSettings(res.data);
    });
    system.info().then((res) => {
      setSystemInfo(res.data);
    });
    system.help().then((res) => {
      setHelpTexts(res.data);
    });
    system.getGlobalChoices().then((res) => {
      setGlobalChoices(res.data);
    });
  }, []);

  // handleBrowserSelect is no longer needed with native picker
  /*
  const handleBrowserSelect = (path: string) => {
    ...
  };
  */

  const openBrowser = async (type: "source" | "target") => {
    const isMultiple = type === "source";
    const initialPath = type === "source" ? lastSourceDir : lastTargetDir;

    try {
      const res = await system.selectFile(isMultiple, initialPath);
      const path = res.data.path;
      const paths = res.data.paths;

      if (path) {
        if (type === "source") {
          setSourcePath(path);
          config.update({ source_paths: paths });
          const dir = path.substring(0, path.lastIndexOf(navigator.userAgent.includes("Windows") ? "\\" : "/") + 1);
          if (dir) {
            setLastSourceDir(dir);
            localStorage.setItem("lastSourceDir", dir);
          }
        } else {
          setTargetPath(path);
          config.update({ target_path: path });
          const dir = path.substring(0, path.lastIndexOf(navigator.userAgent.includes("Windows") ? "\\" : "/") + 1);
          if (dir) {
            setLastTargetDir(dir);
            localStorage.setItem("lastTargetDir", dir);
          }
        }
      }
    } catch (err) {
      console.error("Failed to open native file picker:", err);
    }
  };


  const toggleProcessor = (proc: string) => {
    const newActive = activeProcessors.includes(proc)
      ? activeProcessors.filter((p) => p !== proc)
      : [...activeProcessors, proc];
    setActiveProcessors(newActive);
    config.update({ processors: newActive });
  };

  const updateSetting = (key: string, value: any) => {
    setAllSettings((prev: any) => ({ ...prev, [key]: value }));
    config.update({ [key]: value });
  };


  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [jobStatus, setJobStatus] = useState<string>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const { job, stop } = useJob(jobId);

  // Derived state from useJob
  // We keep local 'isProcessing' for UI toggle, syncing it with job status
  useEffect(() => {
    if (job.status === 'queued' || job.status === 'running') {
      setIsProcessing(true);
      setJobStatus(job.status);
      setProgress(job.progress * 100);
      // setActiveMediaTab('output'); // Output is now fixed
    } else if (job.status === 'completed') {
      setIsProcessing(false);
      setJobStatus('completed');
      setProgress(100);
      // setActiveMediaTab('output'); // Output is now fixed
      // Fetch final details to get preview URL if needed, 
      // or we can rely on what useJob fetched (it fetches status on init/update)
      // useJob updates 'job' state. 
      // We need preview_url. 'job' state in useJob currently doesn't expose raw data easily 
      // unless we expand JobState.
      // Let's refetch status one last time or expand useJob.
      // For now, let's fetch to be safe and simple.
      execute.getStatus(jobId!).then(res => {
        if (res.data.preview_url) {
          setOutputUrl(res.data.preview_url);
        }
      });
    } else if (job.status === 'failed' || job.status === 'canceled') {
      setIsProcessing(false);
      setJobStatus(job.status);
      if (job.status === 'failed') alert("Job failed.");
    }
  }, [job.status, job.progress, jobId]);

  // Live Preview Logic
  useEffect(() => {
    const fetchPreview = async () => {
      // Only require targetPath and at least one processor
      // sourcePath is optional (not needed for frame-only processors like age_modifier)
      if (targetPath && activeProcessors.length > 0 && !isProcessing) {
        setIsPreviewLoading(true);
        try {
          const res = await execute.preview({
            path: targetPath,
            time_seconds: currentVideoTime
          });
          setPreviewUrl(res.data.preview);
        } catch (err) {
          console.error("Preview failed:", err);
        } finally {
          setIsPreviewLoading(false);
        }
      } else {
        setPreviewUrl(null);
      }
    };

    const debounce = setTimeout(fetchPreview, 500);
    return () => clearTimeout(debounce);
  }, [sourcePath, targetPath, currentVideoTime, isProcessing, activeProcessors, allSettings]);


  const startProcessing = async () => {
    const needsSource = activeProcessors.some(p => ["face_swapper", "deep_swapper", "lip_syncer", "face_accessory_manager", "makeup_transfer"].includes(p));
    if (!targetPath || (needsSource && !sourcePath)) return;

    setIsProcessing(true);
    setProgress(0);
    setJobStatus("queued");
    setOutputUrl(null);
    // setActiveMediaTab('output'); // Output is now fixed

    try {
      const res = await execute.run();
      // Orchestrator returns 'queued' normally
      if (["queued", "processing", "running"].includes(res.data.status)) {
        setJobId(res.data.job_id);
      } else {
        alert("Unexpected job status: " + res.data.status);
        setIsProcessing(false);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Processing failed: ${err.response?.data?.detail || err.message}`);
      setIsProcessing(false);
    }
  };

  return (
    <div className="grid h-screen overflow-hidden bg-neutral-950 text-white font-sans p-3 gap-3" style={{ gridTemplateColumns: '30% 1fr 30%' }}>
      <Terminal isOpen={isTerminalOpen} onToggle={() => setIsTerminalOpen(false)} jobId={jobId} />

      {/* Column 1: Processors & Execution */}
      <aside className="flex flex-col h-full overflow-hidden">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
          {/* Processor Tabs */}
          <div className="flex border-b border-neutral-800 bg-neutral-950/20 shrink-0">
            {[
              { id: "face", label: "Face & Portrait", icon: User },
              { id: "frame", label: "Frame & Scene", icon: Film }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveProcessorTab(tab.id)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-3 text-[10px] font-bold uppercase tracking-wider transition-all relative",
                  activeProcessorTab === tab.id
                    ? "text-blue-500 bg-blue-500/5"
                    : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/30"
                )}
              >
                <tab.icon size={14} />
                <span className="hidden sm:inline">{tab.label}</span>
                {activeProcessorTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 animate-in fade-in slide-in-from-bottom-1" />
                )}
              </button>
            ))}
          </div>

          <div className="p-3 space-y-4 flex flex-col h-full overflow-hidden min-h-0">
            <section className="shrink-0 space-y-4">
              {/* Face & Portrait Processors */}
              {activeProcessorTab === "face" && (
                <div className="space-y-2 animate-in fade-in slide-in-from-left-2 duration-300">
                  <div className="grid grid-cols-2 gap-2">
                    {processors
                      .filter(p => !['frame_enhancer', 'background_remover', 'watermark_remover', 'frame_colorizer', 'background_blur', 'color_matcher', 'face_stabilizer', 'grain_matcher', 'privacy_blur', 'frame_expander'].includes(p))
                      .map((proc) => {
                        const Icon = {
                          face_swapper: Replace,
                          face_enhancer: Sparkles,
                          face_debugger: Bug,
                          expression_restorer: Smile,
                          age_modifier: Clock,
                          lip_syncer: Mic2,
                          face_accessory_manager: Box,
                          makeup_transfer: Palette
                        }[proc] || User;

                        return (
                          <Tooltip key={proc} content={helpTexts[proc]}>
                            <button
                              onClick={() => toggleProcessor(proc)}
                              className={`h-10 px-2 text-xs font-medium rounded-lg border transition-all truncate flex items-center justify-center gap-2 ${activeProcessors.includes(proc)
                                ? "bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-900/20"
                                : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                                }`}
                            >
                              <Icon size={14} />
                              <span className="truncate">
                                {proc
                                  .split("_")
                                  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                                  .join(" ")}
                              </span>
                            </button>
                          </Tooltip>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* Frame & Scene Processors */}
              {activeProcessorTab === "frame" && (
                <div className="space-y-2 animate-in fade-in slide-in-from-right-2 duration-300">
                  <div className="grid grid-cols-2 gap-2">
                    {processors
                      .filter(p => ['frame_enhancer', 'background_remover', 'watermark_remover', 'frame_colorizer', 'background_blur', 'color_matcher', 'face_stabilizer', 'grain_matcher', 'privacy_blur', 'frame_expander'].includes(p))
                      .map((proc) => {
                        const Icon = {
                          frame_enhancer: AppWindow,
                          background_remover: Eraser,
                          watermark_remover: Eraser,
                          frame_colorizer: Palette,
                          background_blur: AppWindow,
                          privacy_blur: AppWindow
                        }[proc] || Box;

                        return (
                          <Tooltip key={proc} content={helpTexts[proc]}>
                            <button
                              onClick={() => toggleProcessor(proc)}
                              className={`h-10 px-2 text-xs font-medium rounded-lg border transition-all truncate flex items-center justify-center gap-2 ${activeProcessors.includes(proc)
                                ? "bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-900/20"
                                : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                                }`}
                            >
                              <Icon size={14} />
                              <span className="truncate">
                                {proc
                                  .split("_")
                                  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                                  .join(" ")}
                              </span>
                            </button>
                          </Tooltip>
                        );
                      })}
                  </div>
                </div>
              )}
            </section>

            <section className="flex-1 overflow-y-auto custom-scrollbar -mx-2 px-2 min-h-0">
              <ProcessorSettings
                activeProcessors={activeProcessors}
                currentSettings={allSettings}
                onUpdate={updateSetting}
                helpTexts={helpTexts}
              />
            </section>


          </div>


        </div>
      </aside>

      {/* Column 2: Settings */}
      <div className="h-full flex flex-col gap-3 overflow-hidden">
        <div className="flex-1 min-h-0">
          <SettingsPanel
            settings={allSettings}
            choices={globalChoices}
            helpTexts={helpTexts}
            systemInfo={systemInfo}
            onChange={updateSetting}
            currentTargetPath={targetPath}
          />
        </div>

        {/* Execution Controls - Common to all tabs */}
        <div className="p-2 bg-neutral-900/50 border border-neutral-800 rounded-xl flex items-center gap-2 shrink-0 shadow-lg shadow-black/20">
          <TerminalButton
            isOpen={isTerminalOpen}
            onToggle={() => setIsTerminalOpen(!isTerminalOpen)}
            isProcessing={isProcessing}
            className="w-10 h-10 rounded-lg"
          />
          {showStopConfirm ? (
            <div className="flex-1 flex gap-2 animate-in fade-in zoom-in-95 duration-200">
              <button
                onClick={async () => {
                  await stop();
                  setShowStopConfirm(false);
                }}
                className="flex-1 py-2.5 font-bold rounded-lg bg-blue-600/90 text-white hover:bg-blue-600 transition flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20 backdrop-blur-sm text-sm"
              >
                <X size={14} /> Confirm
              </button>
              <button
                onClick={() => setShowStopConfirm(false)}
                className="px-4 py-2.5 font-bold rounded-lg bg-neutral-800 text-neutral-300 hover:bg-neutral-700 transition text-sm"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                if (isProcessing) {
                  setShowStopConfirm(true);
                } else {
                  startProcessing();
                }
              }}
              disabled={!isProcessing && (!targetPath || (activeProcessors.some(p => ["face_swapper", "deep_swapper", "lip_syncer", "makeup_transfer"].includes(p)) && !sourcePath))}
              className={cn(
                "flex-1 py-2.5 font-bold rounded-lg transition-all duration-200 flex items-center justify-center gap-2 relative overflow-hidden shadow-sm text-sm",
                isProcessing
                  ? "bg-blue-600/10 border border-blue-500/50 text-blue-500 hover:bg-blue-600/20 shadow-blue-500/10"
                  : (!targetPath || (activeProcessors.some(p => ["face_swapper", "deep_swapper", "lip_syncer", "makeup_transfer"].includes(p)) && !sourcePath)
                    ? "bg-neutral-800 text-neutral-500 cursor-not-allowed border border-transparent"
                    : "bg-white text-black hover:bg-neutral-100 border border-transparent shadow-white/5 hover:shadow-white/10")
              )}
            >
              {isProcessing && (
                <div
                  className="absolute inset-0 bg-blue-500/10 transition-all duration-300 ease-linear origin-left"
                  style={{ width: `${progress}%` }}
                />
              )}
              {isProcessing ? (
                <X size={14} className="z-10" />
              ) : (
                <Play size={14} className="fill-current" />
              )}
              <span className="z-10 relative uppercase tracking-wide text-xs">
                {isProcessing ? `Stop Processing (${Math.round(progress)}%)` : "Start Processing"}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Column 3: Source / Target / Preview */}
      <div className="h-full flex flex-col gap-3 min-w-0">

        {/* TOP HALF: Source / Target Tabs */}
        <div className="flex-1 flex flex-col overflow-hidden bg-neutral-900 border border-neutral-800 rounded-xl min-h-0">
          <div className="flex border-b border-neutral-800 bg-neutral-950/20 shrink-0">
            {[
              { id: 'source', label: 'Source', icon: User },
              { id: 'target', label: 'Target', icon: Film }
            ].map((tab: any) => (
              <button
                key={tab.id}
                onClick={() => setActiveMediaTab(tab.id as any)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 py-3 text-[10px] font-bold uppercase tracking-wider transition-all relative",
                  activeMediaTab === tab.id
                    ? "text-blue-500 bg-blue-500/5"
                    : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/30"
                )}
              >
                <tab.icon size={14} />
                <span className="hidden sm:inline">{tab.label}</span>
                {activeMediaTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 animate-in fade-in slide-in-from-bottom-1" />
                )}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden relative p-3">
            {/* Source Tab */}
            {activeMediaTab === 'source' && (
              <div className="h-full animate-in fade-in slide-in-from-left-2 duration-300">
                <div
                  className={cn(
                    "bg-neutral-900 rounded-xl border-2 border-dashed border-neutral-800 flex flex-col items-center justify-center cursor-pointer transition-all h-full group relative overflow-hidden",
                    sourcePath ? "border-blue-500/30 bg-black/40" : "hover:border-neutral-700 hover:bg-neutral-800/50"
                  )}
                >
                  {sourcePath ? (
                    <>
                      <div className="absolute inset-0 z-0">
                        {isVideo(sourcePath) ? (
                          <video
                            src={files.preview(sourcePath)}
                            className="w-full h-full object-contain pointer-events-auto"
                            controls
                            muted
                            loop
                          />
                        ) : (
                          <img
                            src={files.preview(sourcePath)}
                            className="w-full h-full object-contain"
                          />
                        )}
                      </div>

                      <div className="z-10 flex flex-col p-3 w-full h-full justify-start items-start pointer-events-none">
                        <div
                          onClick={() => openBrowser("source")}
                          className="group/filename flex items-center gap-2 cursor-pointer pointer-events-auto bg-black/40 hover:bg-black/60 px-2 py-1 rounded backdrop-blur-sm transition-colors border border-white/5 hover:border-white/20"
                        >
                          <span className="text-[10px] font-bold text-white uppercase tracking-widest truncate max-w-[150px] drop-shadow-md">
                            {sourcePath.split('/').pop()}
                          </span>
                          <Replace size={10} className="text-white/50 group-hover:text-white transition-colors" />
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSourcePath(null);
                            config.update({ source_paths: [] });
                          }}
                          className="absolute top-3 right-3 p-1.5 rounded-full bg-black/50 text-white/70 hover:bg-blue-600 hover:text-white transition-colors pointer-events-auto shadow-lg backdrop-blur-sm z-20"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </>
                  ) : (
                    <div
                      onClick={() => openBrowser("source")}
                      className="flex flex-col items-center justify-center w-full h-full"
                    >
                      <Upload className="text-neutral-600 mb-4 group-hover:text-blue-500 transition-colors" size={32} />
                      <p className="text-sm font-bold text-neutral-400 uppercase tracking-widest">Select Source</p>
                      <p className="text-[10px] text-neutral-600 mt-1 italic">Image or Video</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Target Tab */}
            {activeMediaTab === 'target' && (
              <div className="h-full flex flex-col gap-3 animate-in fade-in duration-300">
                <div className="flex-1 min-h-0">
                  <MediaPreview
                    file={targetPath}
                    type="target"
                    label="Select Target"
                    onUpload={() => openBrowser("target")}
                    onClear={() => {
                      setTargetPath(null);
                      config.update({ target_path: null });
                    }}
                    isMasking={activeProcessors.includes('watermark_remover')}
                    maskArea={[
                      allSettings.watermark_remover_area_start?.[0] || 0,
                      allSettings.watermark_remover_area_start?.[1] || 0,
                      allSettings.watermark_remover_area_end?.[0] || 0,
                      allSettings.watermark_remover_area_end?.[1] || 0
                    ]}
                    onMaskChange={(area) => {
                      updateSetting('watermark_remover_area_start', [area[0], area[1]]);
                      updateSetting('watermark_remover_area_end', [area[2], area[3]]);
                    }}
                    onTimeUpdate={setCurrentVideoTime}
                    className="h-full"
                  />
                </div>

                {/* Detected Faces Card */}
                {/* Conditionally render height or make it collapsible if space is tight */}
                <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-3 h-[120px] shrink-0 flex flex-col">
                  <FaceSelector
                    targetPath={targetPath}
                    currentTime={currentVideoTime}
                    onSelect={(index) => updateSetting("reference_face_position", index)}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* BOTTOM HALF: Output / Preview */}
        <div className="h-[45%] bg-neutral-900 rounded-xl border border-neutral-800 flex flex-col relative overflow-hidden shadow-inner shrink-0">
          {/* Header for Output */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-neutral-800 bg-neutral-950/20">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 flex items-center gap-2">
              <Play size={14} /> Output Preview
            </span>

            {previewUrl && (
              <div className="flex items-center gap-2">
                <select
                  value={previewResolution}
                  onChange={(e) => setPreviewResolution(e.target.value)}
                  className="bg-black/60 backdrop-blur-md text-white/90 text-[10px] font-bold uppercase rounded-lg border border-white/10 px-2 py-1 outline-none hover:bg-black/80 transition-colors"
                >
                  {(globalChoices?.preview_resolutions || ["512x512"]).map((res: string) => (
                    <option key={res} value={res} className="bg-neutral-900">{res}</option>
                  ))}
                </select>

                {isPreviewLoading && (
                  <Loader2 size={12} className="animate-spin text-blue-500" />
                )}
              </div>
            )}
          </div>

          <div className="flex-1 relative overflow-hidden flex items-center justify-center bg-black/20">
            {outputUrl ? (
              <div className="w-full h-full relative group">
                <video
                  src={`http://localhost:8002${outputUrl}`}
                  controls
                  className="w-full h-full object-contain"
                  autoPlay
                />
                <a
                  href={`http://localhost:8002${outputUrl}`}
                  download
                  className="absolute bottom-4 right-4 bg-white text-black px-4 py-2 rounded-full font-bold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2 text-xs"
                >
                  <Upload size={14} className="rotate-180" /> Download
                </a>
              </div>
            ) : isProcessing ? (
              <div className="flex flex-col items-center gap-4 text-neutral-400 w-full max-w-md px-8 scale-90">
                <div className="flex flex-col items-center gap-2">
                  <Loader2 size={32} className="animate-spin text-blue-500" />
                  <p className="text-sm font-medium animate-pulse">Processing...</p>
                </div>

                <div className="w-full space-y-1">
                  <div className="flex justify-between text-[10px] uppercase font-bold text-neutral-500">
                    <span>Progress</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-neutral-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 transition-all duration-300 ease-linear rounded-full"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-center text-[10px] text-neutral-600">
                    {jobStatus === 'queued' ? 'Waiting...' : 'Rendering...'}
                  </p>
                </div>
              </div>
            ) : previewUrl ? (
              <div className="w-full h-full relative group animate-in fade-in duration-500 flex items-center justify-center">
                <img src={previewUrl} className="w-full h-full object-contain" />
                <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded border border-white/10 flex items-center gap-1.5 pointer-events-none">
                  <Sparkles size={10} className="text-blue-500" />
                  <span className="text-[8px] font-bold uppercase tracking-widest text-white/90">Preview</span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-neutral-700 space-y-2">
                <Play size={32} className="opacity-20" />
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-50">Ready</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div >
  );
}

export default App;
