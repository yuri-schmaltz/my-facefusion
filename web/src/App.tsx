import { useState, useEffect } from "react";
import { config, files, execute } from "@/services/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Copy, Upload, Wand2, Play, Loader2, Settings, Replace, Sparkles, AppWindow, Bug, Smile, Clock, Eraser, Palette, Mic2, Box } from "lucide-react";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Terminal } from "@/components/Terminal";

const isVideo = (path: string) => {
  return path.match(/\.(mp4|webm|ogg|mov)$/i);
};

export default function App() {
  const [processors, setProcessors] = useState<string[]>([]);
  const [activeProcessors, setActiveProcessors] = useState<string[]>([]);
  const [sourcePath, setSourcePath] = useState<string | null>(null);
  const [targetPath, setTargetPath] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    config.getProcessors().then((res) => {
      setProcessors(res.data.available);
      setActiveProcessors(res.data.active || []);
    });
  }, []);

  const handleUpload = async (file: File, type: "source" | "target") => {
    const res = await files.upload(file, type);
    if (type === "source") setSourcePath(res.data.path);
    else setTargetPath(res.data.path);
  };

  const toggleProcessor = (proc: string) => {
    const newActive = activeProcessors.includes(proc)
      ? activeProcessors.filter((p) => p !== proc)
      : [...activeProcessors, proc];
    setActiveProcessors(newActive);
    config.update({ processors: newActive });
  };

  const startProcessing = async () => {
    if (!sourcePath || !targetPath) return;
    setIsProcessing(true);
    try {
      const res = await execute.run();
      if (res.data.status === "completed") {
        setOutputUrl(res.data.preview_url);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-neutral-950 text-white font-sans">
      <Terminal />
      {/* Sidebar */}
      <aside className="w-80 border-r border-neutral-800 p-6 space-y-8 flex flex-col h-screen">
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

        {/* Center Column: Settings (Previously Source/Target) */}
        <div className="col-span-5 h-full flex flex-col overflow-hidden">
          <SettingsPanel />
        </div>

        {/* Right Column: Source/Target + Preview */}
        <div className="col-span-7 h-full flex flex-col gap-4 overflow-hidden">

          {/* Top: Source & Target (Side by Side) */}
          {/* Top: Source & Target (Side by Side) */}
          <div className="grid grid-cols-2 gap-4 shrink-0 h-72">
            <Card className="bg-neutral-900/50 border-neutral-800 flex flex-col h-full overflow-hidden">
              <CardHeader className="text-neutral-300 font-semibold flex items-center gap-2 py-3 px-4 shrink-0">
                <Upload size={16} /> Source
              </CardHeader>
              <CardContent className="flex-1 p-0 relative min-h-0 bg-black/50">
                <div className="w-full h-full flex flex-col items-center justify-center text-neutral-500 hover:bg-white/5 transition relative group p-2">
                  <input
                    type="file"
                    className="absolute inset-0 opacity-0 cursor-pointer z-20"
                    onChange={(e) =>
                      e.target.files && handleUpload(e.target.files[0], "source")
                    }
                  />
                  {sourcePath ? (
                    isVideo(sourcePath) ? (
                      <video
                        src={files.preview(sourcePath)}
                        className="w-full h-full object-contain rounded-md"
                        controls
                      />
                    ) : (
                      <img
                        src={files.preview(sourcePath)}
                        alt="Source"
                        className="w-full h-full object-contain rounded-md"
                      />
                    )
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <Copy size={20} />
                      <span className="text-xs">Drop source</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-neutral-900/50 border-neutral-800 flex flex-col h-full overflow-hidden">
              <CardHeader className="text-neutral-300 font-semibold flex items-center gap-2 py-3 px-4 shrink-0">
                <Upload size={16} /> Target
              </CardHeader>
              <CardContent className="flex-1 p-0 relative min-h-0 bg-black/50">
                <div className="w-full h-full flex flex-col items-center justify-center text-neutral-500 hover:bg-white/5 transition relative group p-2">
                  <input
                    type="file"
                    className="absolute inset-0 opacity-0 cursor-pointer z-20"
                    onChange={(e) =>
                      e.target.files && handleUpload(e.target.files[0], "target")
                    }
                  />
                  {targetPath ? (
                    isVideo(targetPath) ? (
                      <video
                        src={files.preview(targetPath)}
                        className="w-full h-full object-contain rounded-md"
                        controls
                      />
                    ) : (
                      <img
                        src={files.preview(targetPath)}
                        alt="Target"
                        className="w-full h-full object-contain rounded-md"
                      />
                    )
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <Wand2 size={20} />
                      <span className="text-xs">Drop target</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Bottom: Preview (Fills remaining) */}
          <div className="bg-neutral-900 rounded-xl border border-neutral-800 flex items-center justify-center relative overflow-hidden flex-1 min-h-0">
            {outputUrl ? (
              <video
                src={`http://localhost:8000${outputUrl}`}
                controls
                className="w-full h-full object-contain"
                autoPlay
              />
            ) : isProcessing ? (
              <div className="flex flex-col items-center gap-4 text-neutral-400">
                <Loader2 size={48} className="animate-spin text-red-500" />
                <p>Generating Deepfake...</p>
              </div>
            ) : (
              <>
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-neutral-800/30 to-transparent pointer-events-none" />
                <p className="text-neutral-600 font-medium z-10">Output Preview</p>
              </>
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
