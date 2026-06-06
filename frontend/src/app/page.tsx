"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  LayoutDashboard,
  PlusCircle,
  FolderOpen,
  Settings,
  User,
  Bell,
  LogOut,
  Search,
  Upload,
  RefreshCw,
  Play,
  Pause,
  Video,
  Image as ImageIcon,
  CheckCircle,
  AlertCircle,
  Sliders,
  ChevronDown,
  Maximize2,
  Volume2
} from "lucide-react";

interface Job {
  id: string;
  type: string;
  status: "idle" | "processing" | "completed" | "failed";
  progress: number;
  time?: string;
}

export default function Home() {
  // Configurações do Estado
  const [sourceImage, setSourceImage] = useState<string | null>(null);
  const [sourceImageFullPath, setSourceImageFullPath] = useState<string | null>(null);
  const [sourceImageName, setSourceImageName] = useState<string>("");

  const [targetVideo, setTargetVideo] = useState<string | null>(null);
  const [targetVideoFullPath, setTargetVideoFullPath] = useState<string | null>(null);
  const [targetVideoName, setTargetVideoName] = useState<string>("");
  
  const [faceSwapperWeight, setFaceSwapperWeight] = useState(0.85);
  const [faceMaskBlur, setFaceMaskBlur] = useState(12);
  const [detectionThreshold, setDetectionThreshold] = useState(0.70);
  const [smoothing, setSmoothing] = useState(5);

  const [outputFormat, setOutputFormat] = useState("MP4");
  const [outputQuality, setOutputQuality] = useState("High");
  const [outputResolution, setOutputResolution] = useState("1080p");

  // Comparador de Antes/Depois (posição da barra central de slide)
  const [sliderPosition, setSliderPosition] = useState(65);
  const [isSliding, setIsSliding] = useState(false);
  const sliderContainerRef = useRef<HTMLDivElement>(null);

  // Vídeo Player
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  // Lista de Jobs no Dashboard
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Status de Hardware e Output
  const [hardwareInfo, setHardwareInfo] = useState<string>("Buscando informações de hardware...");
  const [previewOutputUrl, setPreviewOutputUrl] = useState<string | null>(null);

  const sourceInputRef = useRef<HTMLInputElement>(null);
  const targetInputRef = useRef<HTMLInputElement>(null);

  // Buscar informações do hardware ao montar
  useEffect(() => {
    const fetchHardware = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/hardware/devices");
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            const device = data[0];
            let tempStr = "N/A";
            if (device.temperature) {
              if (typeof device.temperature === "object") {
                const gpuTemp = device.temperature.gpu?.value;
                if (gpuTemp !== undefined) {
                  tempStr = `${gpuTemp}°C`;
                }
              } else {
                tempStr = `${device.temperature}°C`;
              }
            }
            setHardwareInfo(`GPU: ${device.name || "NVIDIA"} | Uso: ${device.load || 0}% | Temp: ${tempStr}`);
          } else {
            const resProv = await fetch("http://localhost:8000/api/hardware/providers");
            if (resProv.ok) {
              const providers = await resProv.json();
              setHardwareInfo(`Hardware: ${providers.join(", ")}`);
            }
          }
        }
      } catch (e) {
        setHardwareInfo("Hardware: CPU (sem aceleração)");
      }
    };
    fetchHardware();
  }, []);

  // Buscar e atualizar lista de Jobs periodimente
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/jobs");
        if (res.ok) {
          const data = await res.json();
          const mappedJobs = data.map((job: any) => ({
            id: job.id,
            type: "Face Swap",
            status: job.status,
            progress: job.progress,
            time: job.status === "processing" ? "Processando..." : undefined,
            outputUrl: job.output ? "http://localhost:8000" + job.output : undefined
          }));
          setJobs(mappedJobs);
          
          const isAnyProcessing = mappedJobs.some((j: any) => j.status === "processing" || j.status === "queued");
          setIsGenerating(isAnyProcessing);
        }
      } catch (err) {
        console.error("Erro ao buscar jobs:", err);
      }
    };

    fetchJobs();
    const interval = setInterval(fetchJobs, 2000);
    return () => clearInterval(interval);
  }, []);

  // Pegar o último job completo para exibição no preview
  useEffect(() => {
    const completedJobs = jobs.filter(j => j.status === "completed" && j.outputUrl);
    if (completedJobs.length > 0) {
      // Definir o mais recente
      setPreviewOutputUrl(completedJobs[0].outputUrl || null);
    }
  }, [jobs]);

  // Lógica do Slider Deslizante (Comparação)
  const handleSliderMove = (clientX: number) => {
    if (!sliderContainerRef.current) return;
    const rect = sliderContainerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!isSliding) return;
    handleSliderMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isSliding) return;
    handleSliderMove(e.clientX);
  };

  const handleMouseUp = () => {
    setIsSliding(false);
  };

  useEffect(() => {
    if (isSliding) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isSliding]);

  // Enviar arquivo para a API
  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("http://localhost:8000/api/media/upload", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      throw new Error("Falha no upload do arquivo.");
    }
    return await res.json();
  };

  const handleSourceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const data = await uploadFile(file);
      setSourceImage("http://localhost:8000" + data.url);
      setSourceImageFullPath(data.file_path);
      setSourceImageName(data.filename);
    } catch (err) {
      alert("Erro ao enviar a imagem de origem: " + err);
    }
  };

  const handleTargetUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const data = await uploadFile(file);
      setTargetVideo("http://localhost:8000" + data.url);
      setTargetVideoFullPath(data.file_path);
      setTargetVideoName(data.filename);
    } catch (err) {
      alert("Erro ao enviar a mídia de destino: " + err);
    }
  };

  // Iniciar processamento
  const handleGenerateSwap = async () => {
    if (isGenerating) return;
    if (!sourceImageFullPath || !targetVideoFullPath) {
      alert("Por favor, envie a imagem de origem e a mídia de destino antes de iniciar.");
      return;
    }
    setIsGenerating(true);
    try {
      const res = await fetch("http://localhost:8000/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_paths: [sourceImageFullPath],
          target_path: targetVideoFullPath,
          face_swapper_weight: faceSwapperWeight,
          face_mask_blur: faceMaskBlur / 50.0, // Normalizar para 0.0 - 1.0 (o slider vai até 50)
          detection_threshold: detectionThreshold,
          smoothing: smoothing,
          processors: ["face_swapper"],
          output_format: outputFormat.toLowerCase()
        })
      });
      if (!res.ok) {
        throw new Error("Erro ao enviar a tarefa para o servidor.");
      }
      const data = await res.json();
      console.log("Job enviado com sucesso:", data);
      setPreviewOutputUrl(null); // Resetar preview até o novo job terminar
    } catch (err) {
      alert("Falha ao iniciar processamento: " + err);
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-[#ededed] font-sans overflow-hidden">
      
      {/* 1. Sidebar Translúcido (Glassmorphism) */}
      <aside className="w-64 bg-zinc-950/40 backdrop-blur-xl border-r border-zinc-900 flex flex-col justify-between p-6">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10 px-2">
            <div className="w-9 h-9 bg-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-600/30">
              <span className="font-extrabold text-white text-lg">F</span>
            </div>
            <h1 className="font-bold text-xl tracking-tight text-white">
              Face<span className="text-red-500">Fusion</span>
            </h1>
          </div>

          {/* Links de Navegação */}
          <nav className="space-y-1">
            <button className="w-full flex items-center gap-3 px-4 py-3 text-zinc-200 bg-zinc-900/50 border-l-2 border-red-500 rounded-lg text-sm font-semibold transition-all">
              <LayoutDashboard size={18} className="text-red-500" />
              Dashboard
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30 rounded-lg text-sm font-semibold transition-all">
              <PlusCircle size={18} />
              Criar Novo
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30 rounded-lg text-sm font-semibold transition-all">
              <FolderOpen size={18} />
              Projetos
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30 rounded-lg text-sm font-semibold transition-all">
              <Settings size={18} />
              Configurações
            </button>
          </nav>
        </div>

        {/* Footer Sidebar (User Info) */}
        <div className="border-t border-zinc-900 pt-6 space-y-4">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-zinc-800 rounded-full flex items-center justify-center border border-zinc-700">
                <User size={18} className="text-zinc-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Yuri S.</p>
                <p className="text-xs text-zinc-500">Administrador</p>
              </div>
            </div>
            <button className="text-zinc-400 hover:text-red-500 transition-colors">
              <Bell size={18} />
            </button>
          </div>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg text-sm font-semibold transition-all">
            <LogOut size={18} />
            Deslogar
          </button>
        </div>
      </aside>

      {/* 2. Main Content Dashboard */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* Header Superior */}
        <header className="h-20 border-b border-zinc-900 px-8 flex items-center justify-between">
          <div className="flex items-center gap-4 bg-zinc-950/50 border border-zinc-900 rounded-lg px-4 py-2 w-96">
            <Search size={18} className="text-zinc-500" />
            <input
              type="text"
              placeholder="Buscar projetos ou logs..."
              className="bg-transparent border-none outline-none text-sm w-full text-zinc-300 placeholder-zinc-500"
            />
          </div>

          <div className="flex items-center gap-4">
            {/* Status do Hardware */}
            <div className="flex items-center gap-2 bg-zinc-950/60 border border-zinc-900 rounded-full px-4 py-1.5 text-xs font-semibold text-zinc-400">
              <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
              {hardwareInfo}
            </div>
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          
          {/* Seção 1: Monitoramento da Fila de Jobs */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white tracking-tight">Fila de Tarefas</h2>
              <span className="text-xs text-zinc-500 font-medium">Status da plataforma</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {jobs.map(job => (
                <div key={job.id} className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-sm text-white">{job.id}</h3>
                      <p className="text-xs text-zinc-500">{job.type}</p>
                    </div>
                    {job.status === "processing" ? (
                      <span className="text-xs bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2.5 py-1 rounded-full font-bold animate-pulse">
                        Processando
                      </span>
                    ) : job.status === "queued" ? (
                      <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-1 rounded-full font-bold">
                        Na Fila
                      </span>
                    ) : job.status === "completed" ? (
                      <span className="text-xs bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2.5 py-1 rounded-full font-bold flex items-center gap-1.5">
                        <CheckCircle size={12} /> Concluído
                      </span>
                    ) : (
                      <span className="text-xs bg-red-500/10 text-red-500 border border-red-500/20 px-2.5 py-1 rounded-full font-bold flex items-center gap-1.5">
                        <AlertCircle size={12} /> Falhou
                      </span>
                    )}
                  </div>

                  {/* Barra de Progresso */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-zinc-400">
                      <span>Progresso</span>
                      <span>{job.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-zinc-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 rounded-full ${
                          job.status === "completed"
                            ? "bg-emerald-500"
                            : job.status === "queued"
                            ? "bg-blue-500"
                            : job.status === "failed"
                            ? "bg-red-500"
                            : "bg-gradient-to-r from-red-500 to-amber-500"
                        }`}
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    {job.time && (
                      <p className="text-[10px] text-right text-zinc-500 font-medium">{job.time}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Seção 2: Área de Mídia (Upload) e Controles */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Esquerda: Upload e Configuração */}
            <div className="space-y-6">
              
              {/* Media Inputs Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Source Image */}
                <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-5 space-y-4">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Imagem de Origem (Source)</span>
                  
                  <input
                    type="file"
                    ref={sourceInputRef}
                    accept="image/*"
                    className="hidden"
                    onChange={handleSourceUpload}
                  />
                  {sourceImage ? (
                    <div className="relative aspect-square bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex items-center justify-center group">
                      <img
                        src={sourceImage}
                        alt="Source Face"
                        className="object-cover w-full h-full"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center gap-2 transition-all">
                        <p className="text-xs font-semibold text-white truncate max-w-[90%]">{sourceImageName}</p>
                        <button
                          onClick={() => {
                            setSourceImage(null);
                            setSourceImageFullPath(null);
                            setSourceImageName("");
                          }}
                          className="bg-red-600 hover:bg-red-500 text-white text-xs px-3 py-1.5 rounded font-bold transition-all"
                        >
                          Substituir
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div 
                      onClick={() => sourceInputRef.current?.click()}
                      className="border border-dashed border-zinc-800 rounded-lg aspect-square flex flex-col items-center justify-center p-4 hover:border-red-500/40 hover:bg-red-500/5 transition-all group cursor-pointer"
                    >
                      <Upload size={24} className="text-zinc-600 group-hover:text-red-500 mb-2 transition-all" />
                      <p className="text-xs text-zinc-400 font-semibold">Arraste a foto da face</p>
                      <span className="text-[10px] text-zinc-500">ou clique para buscar</span>
                    </div>
                  )}
                </div>

                {/* Target Media */}
                <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-5 space-y-4">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Mídia de Destino (Target)</span>
                  
                  <input
                    type="file"
                    ref={targetInputRef}
                    accept="image/*,video/*"
                    className="hidden"
                    onChange={handleTargetUpload}
                  />
                  {targetVideo ? (
                    <div className="relative aspect-square bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex items-center justify-center group">
                      {targetVideo.match(/\.(mp4|webm|mkv|avi|mov)$/i) ? (
                        <video
                          src={targetVideo}
                          className="object-cover w-full h-full"
                          muted
                          loop
                          autoPlay
                        />
                      ) : (
                        <img
                          src={targetVideo}
                          alt="Target Media"
                          className="object-cover w-full h-full"
                        />
                      )}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col justify-center items-center gap-2 transition-all">
                        <div className="text-center px-2">
                          <p className="text-xs font-semibold text-white truncate max-w-[150px]">{targetVideoName}</p>
                        </div>
                        <button
                          onClick={() => {
                            setTargetVideo(null);
                            setTargetVideoFullPath(null);
                            setTargetVideoName("");
                          }}
                          className="bg-red-600 hover:bg-red-500 text-white text-xs px-3 py-1.5 rounded font-bold transition-all"
                        >
                          Substituir
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div 
                      onClick={() => targetInputRef.current?.click()}
                      className="border border-dashed border-zinc-800 rounded-lg aspect-square flex flex-col items-center justify-center p-4 hover:border-red-500/40 hover:bg-red-500/5 transition-all group cursor-pointer"
                    >
                      <Upload size={24} className="text-zinc-600 group-hover:text-red-500 mb-2 transition-all" />
                      <p className="text-xs text-zinc-400 font-semibold">Arraste imagem ou vídeo</p>
                      <span className="text-[10px] text-zinc-500">ou clique para buscar</span>
                    </div>
                  )}
                </div>

              </div>

              {/* Parâmetros e Sliders */}
              <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-6 space-y-6">
                <div className="flex items-center gap-2 text-white font-bold border-b border-zinc-900 pb-3">
                  <Sliders size={18} className="text-red-500" />
                  <h3>Ajustes Técnicos do Processador</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Face Swapper Weight */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-zinc-300">Face Swapper Weight</span>
                      <span className="text-red-500 font-mono">{faceSwapperWeight.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={faceSwapperWeight}
                      onChange={e => setFaceSwapperWeight(parseFloat(e.target.value))}
                      className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Face Mask Blur */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-zinc-300">Face Mask Blur</span>
                      <span className="text-red-500 font-mono">{faceMaskBlur}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="50"
                      step="1"
                      value={faceMaskBlur}
                      onChange={e => setFaceMaskBlur(parseInt(e.target.value))}
                      className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Detection Threshold */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-zinc-300">Limiar de Detecção</span>
                      <span className="text-red-500 font-mono">{detectionThreshold.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={detectionThreshold}
                      onChange={e => setDetectionThreshold(parseFloat(e.target.value))}
                      className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Smoothing */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-zinc-300">Suavização (Smoothing)</span>
                      <span className="text-red-500 font-mono">{smoothing}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      step="1"
                      value={smoothing}
                      onChange={e => setSmoothing(parseInt(e.target.value))}
                      className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                </div>
              </div>

            </div>

            {/* Direita: Preview Compartivo */}
            <div className="space-y-6 flex flex-col justify-between">
              
              {/* Preview Area Box */}
              <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-5 flex-1 flex flex-col justify-between space-y-4">
                <div className="flex items-center justify-between text-xs font-bold text-zinc-400 uppercase tracking-wider">
                  <span>Visualização de Resultado</span>
                  <div className="flex gap-2">
                    <span className="text-[10px] bg-red-600/10 text-red-500 border border-red-500/20 px-2 py-0.5 rounded font-bold">1080p</span>
                  </div>
                </div>

                {/* Comparador de Imagem antes/depois */}
                <div 
                  ref={sliderContainerRef}
                  onMouseDown={() => setIsSliding(true)}
                  onTouchStart={() => setIsSliding(true)}
                  className="relative flex-1 aspect-[16/10] bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden select-none cursor-ew-resize"
                >
                  {/* Imagem de Fundo (Depois - Swapped) */}
                  {previewOutputUrl ? (
                    previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                      <video
                        src={previewOutputUrl}
                        className="absolute inset-0 object-cover w-full h-full pointer-events-none"
                        muted
                        loop
                        autoPlay
                      />
                    ) : (
                      <img
                        src={previewOutputUrl}
                        alt="Swapped Face"
                        className="absolute inset-0 object-cover w-full h-full pointer-events-none"
                      />
                    )
                  ) : (
                    <img
                      src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=720"
                      alt="Swapped Face"
                      className="absolute inset-0 object-cover w-full h-full pointer-events-none"
                    />
                  )}
                  <div className="absolute top-3 right-3 bg-black/60 backdrop-blur px-2.5 py-1 rounded text-[10px] font-bold text-white uppercase pointer-events-none">
                    Depois (After)
                  </div>

                  {/* Imagem de Cima (Antes - Original) */}
                  <div 
                    className="absolute inset-0 overflow-hidden pointer-events-none"
                    style={{ width: `${sliderPosition}%` }}
                  >
                    {targetVideo ? (
                      targetVideo.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                        <video
                          src={targetVideo}
                          className="absolute inset-0 object-cover w-full h-full max-w-none pointer-events-none"
                          style={{ width: sliderContainerRef.current?.getBoundingClientRect().width }}
                          muted
                          loop
                          autoPlay
                        />
                      ) : (
                        <img
                          src={targetVideo}
                          alt="Original Face"
                          className="absolute inset-0 object-cover w-full h-full max-w-none pointer-events-none"
                          style={{ width: sliderContainerRef.current?.getBoundingClientRect().width }}
                        />
                      )
                    ) : (
                      <img
                        src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&q=80&w=720"
                        alt="Original Face"
                        className="absolute inset-0 object-cover w-full h-full max-w-none pointer-events-none"
                        style={{ width: sliderContainerRef.current?.getBoundingClientRect().width }}
                      />
                    )}
                    <div className="absolute top-3 left-3 bg-black/60 backdrop-blur px-2.5 py-1 rounded text-[10px] font-bold text-white pointer-events-none">
                      Antes (Before)
                    </div>
                  </div>

                  {/* Barra Central do Slider */}
                  <div 
                    className="absolute top-0 bottom-0 w-[2px] bg-red-500 cursor-ew-resize flex items-center justify-center"
                    style={{ left: `${sliderPosition}%` }}
                  >
                    <div className="w-6 h-6 bg-red-600 rounded-full border border-red-400 flex items-center justify-center shadow-lg cursor-ew-resize">
                      <div className="w-1.5 h-3 flex justify-between">
                        <span className="w-[1px] h-full bg-white/60"></span>
                        <span className="w-[1px] h-full bg-white/60"></span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Controles do Vídeo Player */}
                <div className="flex items-center gap-4 bg-zinc-950/55 border border-zinc-900 rounded-lg p-3">
                  <button 
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="text-zinc-200 hover:text-red-500 transition-colors"
                  >
                    {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                  </button>
                  
                  {/* Slider de Tempo do Vídeo */}
                  <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden relative">
                    <div className="absolute top-0 bottom-0 left-0 bg-red-600 w-1/3"></div>
                  </div>

                  <span className="text-[10px] text-zinc-500 font-mono">00:11 / 00:34</span>
                  
                  <button className="text-zinc-400 hover:text-zinc-200">
                    <Volume2 size={16} />
                  </button>
                  <button className="text-zinc-400 hover:text-zinc-200">
                    <Maximize2 size={16} />
                  </button>
                </div>
              </div>

              {/* Botão de Geração e Configuração de Output */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                {/* Opções de Output */}
                <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-5 space-y-4">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider block">Opções de Exportação</span>
                  
                  <div className="grid grid-cols-3 gap-2">
                    {/* Formato */}
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">Formato</label>
                      <div className="relative">
                        <select 
                          value={outputFormat}
                          onChange={e => setOutputFormat(e.target.value)}
                          className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer"
                        >
                          <option>MP4</option>
                          <option>WEBM</option>
                          <option>MKV</option>
                        </select>
                        <ChevronDown size={12} className="absolute right-2 top-2 text-zinc-500 pointer-events-none" />
                      </div>
                    </div>

                    {/* Qualidade */}
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">Qualidade</label>
                      <div className="relative">
                        <select 
                          value={outputQuality}
                          onChange={e => setOutputQuality(e.target.value)}
                          className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer"
                        >
                          <option>High</option>
                          <option>Medium</option>
                          <option>Low</option>
                        </select>
                        <ChevronDown size={12} className="absolute right-2 top-2 text-zinc-500 pointer-events-none" />
                      </div>
                    </div>

                    {/* Resolução */}
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">Resolução</label>
                      <div className="relative">
                        <select 
                          value={outputResolution}
                          onChange={e => setOutputResolution(e.target.value)}
                          className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer"
                        >
                          <option>1080p</option>
                          <option>720p</option>
                          <option>4K</option>
                        </select>
                        <ChevronDown size={12} className="absolute right-2 top-2 text-zinc-500 pointer-events-none" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Botão de Ação */}
                <button
                  onClick={handleGenerateSwap}
                  disabled={isGenerating}
                  className={`w-full h-14 font-extrabold rounded-xl flex items-center justify-center gap-2 text-white shadow-lg transition-all ${
                    isGenerating
                      ? "bg-zinc-800 border border-zinc-700 cursor-not-allowed text-zinc-500"
                      : "bg-red-600 hover:bg-red-500 hover:scale-[1.02] active:scale-[0.98] shadow-red-600/20 cursor-pointer"
                  }`}
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={18} className="animate-spin text-zinc-500" />
                      PROCESSANDO...
                    </>
                  ) : (
                    <>
                      INICIAR PROCESSAMENTO (SWAP)
                    </>
                  )}
                </button>
              </div>

            </div>

          </div>

        </div>
      </main>

    </div>
  );
}
