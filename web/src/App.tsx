
import { useState, useEffect } from "react";
import { config, files, execute, system } from "@/services/api";
import { Card } from "@/components/ui/card";
import { Upload, Play, Loader2, Replace, Sparkles, AppWindow, Bug, Smile, Clock, Eraser, Palette, Mic2, Box, Info, X } from "lucide-react";
import { SettingsPanel } from "@/components/SettingsPanel";
import { cn } from "@/lib/utils";
import { Terminal, TerminalButton } from "@/components/Terminal";
import { Tooltip } from "@/components/ui/Tooltip";
import ProcessorSettings from "@/components/ProcessorSettings";
import FaceSelector from "@/components/FaceSelector";
// ... imports

// ... inside App component



const isVideo = (path: string) => {
  return path.match(/\.(mp4|webm|ogg|mov)$/i);
};

function App() {
  const [processors, setProcessors] = useState<string[]>([]);
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

  const toggleArrayItem = (key: string, item: string) => {
    const current = (allSettings[key] || []);
    const newer = current.includes(item)
      ? current.filter((i: string) => i !== item)
      : [...current, item];

    updateSetting(key, newer);
  };

  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [jobStatus, setJobStatus] = useState<string>("idle");

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isProcessing && jobId) {
      interval = setInterval(async () => {
        try {
          const res = await execute.getJobStatus(jobId);
          const status = res.data.status;
          const currentProgress = res.data.progress || 0;

          setProgress(currentProgress);
          setJobStatus(status);

          if (status === "completed") {
            setIsProcessing(false);
            setOutputUrl(res.data.preview_url);
            clearInterval(interval);
          } else if (status === "failed") {
            setIsProcessing(false);
            alert("Job failed during processing.");
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Failed to poll job status:", err);
        }
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [isProcessing, jobId]);

  const startProcessing = async () => {
    if (!sourcePath || !targetPath) return;
    setIsProcessing(true);
    setProgress(0);
    setJobStatus("processing");
    setOutputUrl(null); // Clear previous output
    try {
      const res = await execute.run();
      if (res.data.status === "processing") {
        setJobId(res.data.job_id);
      } else {
        // Fallback for sync
        alert("Job finished immediately (sync mode?)");
        setIsProcessing(false);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Processing failed: ${err.response?.data?.detail || err.message}`);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-neutral-950 text-white font-sans">
      <Terminal isOpen={isTerminalOpen} onToggle={() => setIsTerminalOpen(false)} />

      {/* Sidebar */}
      <aside className="w-[420px] py-3 pl-3 pr-1.5 flex flex-col h-screen overflow-hidden">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col h-full">
          <div className="p-3 space-y-4 flex flex-col h-full overflow-hidden">
            <section className="shrink-0">
              <div className="grid grid-cols-2 gap-2">
                {processors.map((proc) => {
                  const Icon = {
                    face_swapper: Replace,
                    face_enhancer: Sparkles,
                    frame_enhancer: AppWindow,
                    face_debugger: Bug,
                    expression_restorer: Smile,
                    age_modifier: Clock,
                    background_remover: Eraser,
                    watermark_remover: Eraser,
                    frame_colorizer: Palette,
                    lip_syncer: Mic2
                  }[proc] || Box;

                  return (
                    <Tooltip key={proc} content={helpTexts[proc]}>
                      <button
                        onClick={() => toggleProcessor(proc)}
                        className={`h-10 px-2 text-xs font-medium rounded-md border transition-all truncate flex items-center justify-center gap-2 ${activeProcessors.includes(proc)
                          ? "bg-red-600 border-red-500 text-white shadow-md shadow-red-900/20"
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
            </section>

            <section className="flex-1 overflow-y-auto custom-scrollbar -mx-2 px-2 min-h-0">
              <ProcessorSettings
                activeProcessors={activeProcessors}
                currentSettings={allSettings}
                onUpdate={updateSetting}
                helpTexts={helpTexts}
              />
            </section>

            <section className="space-y-2 pt-3 border-t border-neutral-800 shrink-0">
              <div className="flex items-center gap-2">
                <label className="text-xs font-bold text-neutral-400 uppercase tracking-wider block">
                  Execution Provider
                </label>
                <Tooltip content={helpTexts['execution_providers']}>
                  <Info size={12} className="text-neutral-500 cursor-help" />
                </Tooltip>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {["cpu", "cuda", "rocm", "directml", "openvino", "coreml"].map((provider) => {
                  const current = allSettings.execution_providers || [];
                  const isSelected = current.includes(provider);
                  const isAvailable = (systemInfo.execution_providers || ['cpu']).includes(provider);

                  return (
                    <button
                      key={provider}
                      disabled={!isAvailable}
                      onClick={() => {
                        toggleArrayItem("execution_providers", provider);
                      }}
                      className={cn(
                        "px-2 py-1.5 text-[10px] font-bold rounded border text-center transition-all",
                        isSelected
                          ? "bg-red-600/20 border-red-500 text-red-500"
                          : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-300",
                        !isAvailable && "opacity-20 cursor-not-allowed grayscale border-neutral-800"
                      )}
                    >
                      {provider.toUpperCase()}
                      {!isAvailable && <span className="block text-[8px] opacity-50">N/A</span>}
                    </button>
                  )
                })}
              </div>
            </section>
          </div>

          <section className="p-4 bg-neutral-900/50 border-t border-neutral-800 flex items-center gap-2 shrink-0">
            <TerminalButton
              isOpen={isTerminalOpen}
              onToggle={() => setIsTerminalOpen(!isTerminalOpen)}
              isProcessing={isProcessing}
              className="w-14"
            />
            {showStopConfirm ? (
              <div className="flex-1 flex gap-1 animate-in fade-in zoom-in-95 duration-200">
                <button
                  onClick={async () => {
                    await execute.stop();
                    setShowStopConfirm(false);
                  }}
                  className="flex-1 py-4 font-bold rounded-lg bg-red-600 text-white hover:bg-red-700 transition flex items-center justify-center gap-2 shadow-lg shadow-red-900/20"
                >
                  <X size={18} /> Confirm Stop
                </button>
                <button
                  onClick={() => setShowStopConfirm(false)}
                  className="px-6 py-4 font-bold rounded-lg bg-neutral-800 text-neutral-300 hover:bg-neutral-700 transition"
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
                disabled={!isProcessing && (!sourcePath || !targetPath)}
                className={cn(
                  "flex-1 py-4 font-bold rounded-lg transition flex items-center justify-center gap-2 relative overflow-hidden",
                  isProcessing
                    ? "bg-red-600/10 border border-red-500/50 text-red-500 hover:bg-red-600/20"
                    : (!sourcePath || !targetPath
                      ? "bg-neutral-800 text-neutral-500 cursor-not-allowed"
                      : "bg-white text-black hover:bg-neutral-200")
                )}
              >
                {isProcessing && (
                  <div
                    className="absolute inset-0 bg-red-500/10 transition-all duration-300 ease-linear origin-left"
                    style={{ width: `${progress}%` }}
                  />
                )}
                {isProcessing ? (
                  <X size={18} className="z-10" />
                ) : (
                  <Play size={18} />
                )}
                <span className="z-10 relative">
                  {isProcessing ? `Stop Processing (${Math.round(progress)}%)` : "Start Processing"}
                </span>
              </button>
            )}
          </section>
        </div>
      </aside>

      {/* Main Content Layout */}
      <main className="flex-1 py-3 pl-1.5 pr-3 grid grid-cols-12 gap-3 overflow-hidden h-screen">

        {/* Center Column: Settings */}
        <div className="col-span-4 h-full flex flex-col overflow-hidden">
          <SettingsPanel
            helpTexts={helpTexts}
          />
        </div>

        {/* Right Column: Source / Target / Preview */}
        <div className="col-span-8 h-full flex flex-col gap-3 overflow-hidden">
          <div className="grid grid-cols-2 gap-3 h-[250px]">
            {/* Source Card */}
            <div
              className={cn(
                "bg-neutral-900 rounded-xl border-2 border-dashed border-neutral-800 flex flex-col items-center justify-center cursor-pointer transition-all h-full group relative overflow-hidden",
                sourcePath ? "border-red-500/30 bg-black/40" : "hover:border-neutral-700 hover:bg-neutral-800/50"
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
                      className="absolute top-3 right-3 p-1.5 rounded-full bg-black/50 text-white/70 hover:bg-red-600 hover:text-white transition-colors pointer-events-auto shadow-lg backdrop-blur-sm z-20"
                    >
                      <X size={14} />
                    </button>
                    {/* The rest of the card is empty and allows pointer-events-none to pass through to the video below */}
                  </div>
                </>
              ) : (
                <div
                  onClick={() => openBrowser("source")}
                  className="flex flex-col items-center justify-center w-full h-full"
                >
                  <Upload className="text-neutral-600 mb-4 group-hover:text-red-500 transition-colors" size={32} />
                  <p className="text-sm font-bold text-neutral-400 uppercase tracking-widest">Select Source</p>
                  <p className="text-[10px] text-neutral-600 mt-1 italic">Image or Video</p>
                </div>
              )}
            </div>

            {/* Target Card */}
            <div className="flex flex-col h-full overflow-hidden">
              <div
                className={cn(
                  "bg-neutral-900 rounded-xl border-2 border-dashed border-neutral-800 flex flex-col items-center justify-center cursor-pointer transition-all flex-1 group min-h-0 relative overflow-hidden",
                  targetPath ? "border-red-500/30 bg-black/40" : "hover:border-neutral-700 hover:bg-neutral-800/50"
                )}
              >
                {targetPath ? (
                  <>
                    <div className="absolute inset-0 z-0">
                      {isVideo(targetPath) ? (
                        <video
                          src={files.preview(targetPath)}
                          className="w-full h-full object-contain pointer-events-auto"
                          controls
                          muted
                          loop
                        />
                      ) : (
                        <img
                          src={files.preview(targetPath)}
                          className="w-full h-full object-contain"
                        />
                      )}
                    </div>

                    <div className="z-10 flex flex-col p-3 w-full h-full justify-start items-start pointer-events-none">
                      <div
                        onClick={() => openBrowser("target")}
                        className="group/filename flex items-center gap-2 cursor-pointer pointer-events-auto bg-black/40 hover:bg-black/60 px-2 py-1 rounded backdrop-blur-sm transition-colors border border-white/5 hover:border-white/20"
                      >
                        <span className="text-[10px] font-bold text-white uppercase tracking-widest truncate max-w-[150px] drop-shadow-md">
                          {targetPath.split('/').pop()}
                        </span>
                        <Replace size={10} className="text-white/50 group-hover:text-white transition-colors" />
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setTargetPath(null);
                          config.update({ target_path: null });
                        }}
                        className="absolute top-3 right-3 p-1.5 rounded-full bg-black/50 text-white/70 hover:bg-red-600 hover:text-white transition-colors pointer-events-auto shadow-lg backdrop-blur-sm z-20"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </>
                ) : (
                  <div
                    onClick={() => openBrowser("target")}
                    className="flex flex-col items-center justify-center w-full h-full"
                  >
                    <Upload className="text-neutral-600 mb-4 group-hover:text-red-500 transition-colors" size={32} />
                    <p className="text-sm font-bold text-neutral-400 uppercase tracking-widest">Select Target</p>
                    <p className="text-[10px] text-neutral-600 mt-1 italic">The base media</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Detected Faces Card */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-3 animate-in fade-in slide-in-from-top-2 duration-500 min-h-[140px] flex flex-col">
            <FaceSelector
              targetPath={targetPath}
              currentTime={currentVideoTime}
              onSelect={(index) => updateSetting("reference_face_position", index)}
            />
          </div>

          {/* Preview Card */}
          <div className="bg-neutral-900 rounded-xl border border-neutral-800 flex items-center justify-center relative overflow-hidden flex-1 min-h-0 shadow-inner">
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
                  className="absolute bottom-4 right-4 bg-white text-black px-4 py-2 rounded-full font-bold opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2"
                >
                  <Upload size={16} className="rotate-180" /> Download
                </a>
              </div>
            ) : isProcessing ? (
              <div className="flex flex-col items-center gap-6 text-neutral-400 w-full max-w-md px-8">
                <div className="flex flex-col items-center gap-2">
                  <Loader2 size={48} className="animate-spin text-red-500" />
                  <p className="text-lg font-medium animate-pulse">Generating Deepfake...</p>
                </div>

                <div className="w-full space-y-2">
                  <div className="flex justify-between text-xs uppercase font-bold text-neutral-500">
                    <span>Progress</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="h-2 w-full bg-neutral-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-600 transition-all duration-300 ease-linear rounded-full"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-center text-xs text-neutral-600 pt-2">
                    {jobStatus === 'queued' ? 'Waiting in queue...' : 'Processing frames...'}
                  </p>
                </div>
              </div>
            ) : (
              <>
                {/* Assuming the icon mapping object is defined elsewhere and needs to be updated.
                    Since the full context of the icon mapping object (e.g., `face_debugger: Bug,`)
                    is not present in the provided document, this change is placed as a comment
                    to indicate where it would logically go if the object were present.
                    If this mapping is part of a larger object, you would insert
                    `watermark_remover: Eraser, // Reusing Eraser for now or use another icon`
                    into that object.
                */}
                {/*
                // Example of where the icon mapping might be if it existed in this file:
                const iconMapping = {
                  face_debugger: Bug,
                  expression_restorer: Smile,
                  age_modifier: Clock,
                  background_remover: Eraser,
                  watermark_remover: Eraser, // Reusing Eraser for now or use another icon
                  frame_colorizer: Palette,
                  lip_syncer: Mic2,
                };
                */}
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-neutral-800/30 to-transparent pointer-events-none" />
                <p className="text-neutral-600 font-medium z-10 flex items-center gap-2">
                  <Sparkles size={16} /> Output Preview
                </p>
              </>
            )}
          </div>

        </div>
      </main>
    </div >
  );
}

export default App;
