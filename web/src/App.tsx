import { useState, useEffect } from "react";
import { config, files, execute } from "@/services/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Copy, Upload, Wand2, Play, Loader2, Settings } from "lucide-react";
import { SettingsDialog } from "@/components/SettingsDialog";
import { Terminal } from "@/components/Terminal";

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
      <SettingsDialog isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      {/* Sidebar */}
      <aside className="w-80 border-r border-neutral-800 p-6 space-y-8">
        <div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">
            FaceFusion 2.0
          </h1>
          <p className="text-sm text-neutral-500">Premium Interface</p>
        </div>

        <section>
          <h2 className="text-sm font-semibold text-neutral-400 mb-4 uppercase tracking-wider">
            Processors
          </h2>
          <div className="flex flex-wrap gap-2">
            {processors.map((proc) => (
              <button
                key={proc}
                onClick={() => toggleProcessor(proc)}
                className={`px-3 py-1.5 text-xs rounded-full border transition-all ${activeProcessors.includes(proc)
                  ? "bg-red-600 border-red-500 text-white"
                  : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-500"
                  }`}
              >
                {proc}
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="w-full py-2 bg-neutral-900 border border-neutral-800 text-neutral-300 font-medium rounded-lg hover:bg-neutral-800 transition flex items-center justify-center gap-2"
          >
            <Settings size={16} /> Advanced Settings
          </button>

          <button
            onClick={startProcessing}
            disabled={isProcessing || !sourcePath || !targetPath}
            className={`w-full py-3 font-bold rounded-lg transition flex items-center justify-center gap-2 ${isProcessing || !sourcePath || !targetPath
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

      {/* Main Content */}
      <main className="flex-1 p-8 grid grid-cols-2 gap-8">
        {/* Source & Target */}
        <div className="space-y-6">
          <Card className="bg-neutral-900/50 border-neutral-800">
            <CardHeader className="text-neutral-300 font-semibold flex items-center gap-2">
              <Upload size={18} /> Source
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-neutral-700 rounded-lg h-48 flex flex-col items-center justify-center text-neutral-500 hover:border-neutral-500 transition relative overflow-hidden group">
                {sourcePath ? (
                  <img
                    src={files.preview(sourcePath)}
                    alt="Source"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <>
                    <input
                      type="file"
                      className="absolute inset-0 opacity-0 cursor-pointer"
                      onChange={(e) =>
                        e.target.files && handleUpload(e.target.files[0], "source")
                      }
                    />
                    <Copy size={24} className="mb-2" />
                    <span>Drop source image</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900/50 border-neutral-800">
            <CardHeader className="text-neutral-300 font-semibold flex items-center gap-2">
              <Upload size={18} /> Target
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-neutral-700 rounded-lg h-48 flex flex-col items-center justify-center text-neutral-500 hover:border-neutral-500 transition relative overflow-hidden">
                {targetPath ? (
                  <img
                    src={files.preview(targetPath)}
                    alt="Target"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <>
                    <input
                      type="file"
                      className="absolute inset-0 opacity-0 cursor-pointer"
                      onChange={(e) =>
                        e.target.files && handleUpload(e.target.files[0], "target")
                      }
                    />
                    <Wand2 size={24} className="mb-2" />
                    <span>Drop target file</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Preview */}
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 flex items-center justify-center relative overflow-hidden">
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
      </main>
    </div>
  );
}
