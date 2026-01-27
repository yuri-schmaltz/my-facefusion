
import { useState, useEffect } from "react";
import { config, files, execute } from "@/services/api";
import { Card } from "@/components/ui/card";
import { Upload, Play, Loader2, Replace, Sparkles, AppWindow, Bug, Smile, Clock, Eraser, Palette, Mic2, Box } from "lucide-react";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Terminal } from "@/components/Terminal";
import FileBrowserDialog from "./components/FileBrowserDialog";
import ProcessorSettings from "./components/ProcessorSettings";

const isVideo = (path: string) => {
  return path.match(/\.(mp4|webm|ogg|mov)$/i);
};

function App() {
  const [processors, setProcessors] = useState<string[]>([]);
  const [activeProcessors, setActiveProcessors] = useState<string[]>([]);
  const [allSettings, setAllSettings] = useState<any>({});

  // App State
  const [sourcePath, setSourcePath] = useState<string | null>(null);
  const [targetPath, setTargetPath] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);

  // File Browser State
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [browserType, setBrowserType] = useState<"source" | "target">("source");

  // Persist Last Directories
  const [lastSourceDir, setLastSourceDir] = useState<string>(() => localStorage.getItem("lastSourceDir") || "");
  const [lastTargetDir, setLastTargetDir] = useState<string>(() => localStorage.getItem("lastTargetDir") || "");

  useEffect(() => {
    config.getProcessors().then((res) => {
      setProcessors(res.data.available);
      setActiveProcessors(res.data.active || []);
    });
    config.getSettings().then((res) => {
      setAllSettings(res.data);
    });
  }, []);

  const handleBrowserSelect = (path: string) => {
    if (browserType === "source") {
      setSourcePath(path);
      const dir = path.substring(0, path.lastIndexOf(navigator.userAgent.includes("Windows") ? "\\" : "/") + 1);
      if (dir) {
        setLastSourceDir(dir);
        localStorage.setItem("lastSourceDir", dir);
      }
    } else {
      setTargetPath(path);
      const dir = path.substring(0, path.lastIndexOf(navigator.userAgent.includes("Windows") ? "\\" : "/") + 1);
      if (dir) {
        setLastTargetDir(dir);
        localStorage.setItem("lastTargetDir", dir);
      }
    }
    setIsBrowserOpen(false);
  };

  const openBrowser = (type: "source" | "target") => {
    setBrowserType(type);
    setIsBrowserOpen(true);
  };

  const getInitialPath = () => {
    return browserType === "source" ? lastSourceDir : lastTargetDir;
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

  const startProcessing = async () => {
    if (!sourcePath || !targetPath) return;
    setIsProcessing(true);
    try {
      const res = await execute.run();
      if (res.data.status === "completed") {
        setOutputUrl(res.data.preview_url);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Processing failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-neutral-950 text-white font-sans">
      <Terminal />
      <FileBrowserDialog
        isOpen={isBrowserOpen}
        onClose={() => setIsBrowserOpen(false)}
        onSelect={handleBrowserSelect}
        type={browserType}
        initialPath={getInitialPath()}
      />

      {/* Sidebar */}
      <aside className="w-[420px] border-r border-neutral-800 p-6 space-y-8 flex flex-col h-screen">
        <div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">
            FaceFusion 2.0
          </h1>
          <p className="text-sm text-neutral-500">Premium Interface</p>
        </div>

        <section className="flex-1 overflow-y-auto custom-scrollbar">
          <h2 className="text-sm font-semibold text-neutral-400 mb-4 uppercase tracking-wider">
            Processors
          </h2>
          <div className="grid grid-cols-3 gap-2">
            {processors.map((proc) => {
              const Icon = {
                face_swapper: Replace,
                face_enhancer: Sparkles,
                frame_enhancer: AppWindow,
                face_debugger: Bug,
                expression_restorer: Smile,
                age_modifier: Clock,
                background_remover: Eraser,
                frame_colorizer: Palette,
                lip_syncer: Mic2
              }[proc] || Box;

              return (
                <button
                  key={proc}
                  onClick={() => toggleProcessor(proc)}
                  className={`h-10 px-2 text-xs font-medium rounded-md border transition-all truncate flex items-center justify-center gap-2 ${activeProcessors.includes(proc)
                    ? "bg-red-600 border-red-500 text-white shadow-md shadow-red-900/20"
                    : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                    }`}
                  title={proc}
                >
                  <Icon size={14} />
                  <span className="truncate">
                    {proc
                      .split("_")
                      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(" ")}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="flex-[2] overflow-y-auto custom-scrollbar -mx-2 px-2">
          <ProcessorSettings
            activeProcessors={activeProcessors}
            currentSettings={allSettings}
            onUpdate={updateSetting}
          />
        </section>

        <section className="space-y-4 shrink-0">
          <button
            onClick={startProcessing}
            disabled={isProcessing || !sourcePath || !targetPath}
            className={`w-full py-4 font-bold rounded-lg transition flex items-center justify-center gap-2 ${isProcessing || !sourcePath || !targetPath
              ? "bg-neutral-800 text-neutral-500 cursor-not-allowed"
              : "bg-white text-black hover:bg-neutral-200"
              }`}
          >
            {isProcessing ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Play size={18} />
            )}
            {isProcessing ? "Processing..." : "Start Processing"}
          </button>
        </section>
      </aside>

      {/* Main Content Layout */}
      <main className="flex-1 p-6 grid grid-cols-12 gap-6 overflow-hidden h-screen">

        {/* Center Column: Settings */}
        <div className="col-span-4 h-full flex flex-col overflow-hidden">
          <SettingsPanel />
        </div>

        {/* Right Column: Source / Target / Preview */}
        <div className="col-span-8 h-full flex flex-col gap-6 overflow-hidden">

          {/* Top Row: Source and Target Cards */}
          <div className="grid grid-cols-2 gap-4 h-72 shrink-0">

            {/* Source Card */}
            <Card className="flex flex-col overflow-hidden relative group border-neutral-800 bg-neutral-900/50">
              <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => openBrowser("source")}
                  className="bg-black/50 hover:bg-black/80 text-white p-2 rounded-lg backdrop-blur-sm transition-colors flex items-center gap-2 text-xs"
                >
                  <Upload size={14} /> Change Source
                </button>
              </div>

              <div
                onClick={() => !sourcePath && openBrowser("source")}
                className="flex-1 relative cursor-pointer hover:bg-neutral-900/50 transition-colors"
              >
                {sourcePath ? (
                  <div className="w-full h-full relative bg-black/50 flex items-center justify-center">
                    {isVideo(sourcePath) ? (
                      <video src={files.preview(sourcePath)} className="max-w-full max-h-full w-full h-full object-contain" controls />
                    ) : (
                      <img src={files.preview(sourcePath)} alt="Source" className="max-w-full max-h-full w-full h-full object-contain" />
                    )}
                  </div>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-neutral-500 gap-4">
                    <div className="p-4 rounded-full bg-neutral-900 border border-neutral-800 group-hover:border-blue-500/50 group-hover:text-blue-500 transition-colors">
                      <Upload size={24} />
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-neutral-300">Select Source</p>
                      <p className="text-xs mt-1">Image or Video</p>
                    </div>
                  </div>
                )}
              </div>
              <div className="p-3 border-t border-neutral-800 bg-neutral-900/50 flex justify-between items-center">
                <span className="text-xs font-medium text-neutral-400">Source</span>
                {sourcePath && (
                  <button onClick={() => setSourcePath(null)} className="text-xs text-red-400 hover:text-red-300">Clear</button>
                )}
              </div>
            </Card>

            {/* Target Card */}
            <Card className="flex flex-col overflow-hidden relative group border-neutral-800 bg-neutral-900/50">
              <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => openBrowser("target")}
                  className="bg-black/50 hover:bg-black/80 text-white p-2 rounded-lg backdrop-blur-sm transition-colors flex items-center gap-2 text-xs"
                >
                  <Upload size={14} /> Change Target
                </button>
              </div>

              <div
                onClick={() => !targetPath && openBrowser("target")}
                className="flex-1 relative cursor-pointer hover:bg-neutral-900/50 transition-colors"
              >
                {targetPath ? (
                  <div className="w-full h-full relative bg-black/50 flex items-center justify-center">
                    {isVideo(targetPath) ? (
                      <video src={files.preview(targetPath)} className="max-w-full max-h-full w-full h-full object-contain" controls />
                    ) : (
                      <img src={files.preview(targetPath)} alt="Target" className="max-w-full max-h-full w-full h-full object-contain" />
                    )}
                  </div>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-neutral-500 gap-4">
                    <div className="p-4 rounded-full bg-neutral-900 border border-neutral-800 group-hover:border-emerald-500/50 group-hover:text-emerald-500 transition-colors">
                      <Upload size={24} />
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-neutral-300">Select Target</p>
                      <p className="text-xs mt-1">Image or Video</p>
                    </div>
                  </div>
                )}
              </div>
              <div className="p-3 border-t border-neutral-800 bg-neutral-900/50 flex justify-between items-center">
                <span className="text-xs font-medium text-neutral-400">Target</span>
                {targetPath && (
                  <button onClick={() => setTargetPath(null)} className="text-xs text-red-400 hover:text-red-300">Clear</button>
                )}
              </div>
            </Card>
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
              <div className="flex flex-col items-center gap-4 text-neutral-400">
                <Loader2 size={48} className="animate-spin text-red-500" />
                <p>Generating Deepfake...</p>
              </div>
            ) : (
              <>
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-neutral-800/30 to-transparent pointer-events-none" />
                <p className="text-neutral-600 font-medium z-10 flex items-center gap-2">
                  <Sparkles size={16} /> Output Preview
                </p>
              </>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;
