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
  Volume2,
  VolumeX,
  Trash2,
  Download,
  ExternalLink,
  Cpu,
  Folder,
  Terminal,
  SlidersHorizontal
} from "lucide-react";

interface Job {
  id: string;
  type: string;
  status: "idle" | "processing" | "queued" | "completed" | "failed";
  progress: number;
  time?: string;
  source?: string;
  target?: string;
  outputUrl?: string;
  error_message?: string;
}

export default function Home() {
  // Navegação
  const [activeTab, setActiveTab] = useState<"create_new" | "projects" | "settings">("create_new");

  // Configurações do Estado (Face Swap)
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
  const videoContainerRef = useRef<HTMLDivElement>(null);

  // Vídeo Player & Comparator
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const originalVideoRef = useRef<HTMLVideoElement>(null);
  const swappedVideoRef = useRef<HTMLVideoElement>(null);

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs === 0) return "00:00";
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = Math.floor(secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  // Lista de Jobs no Dashboard
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Status de Hardware e Output
  const [hardwareInfo, setHardwareInfo] = useState<string>("Buscando informações de hardware...");
  const [previewOutputUrl, setPreviewOutputUrl] = useState<string | null>(null);

  const [apiUrl, setApiUrl] = useState("http://localhost:8000");
  const [configLoaded, setConfigLoaded] = useState(false);

  const sourceInputRef = useRef<HTMLInputElement>(null);
  const targetInputRef = useRef<HTMLInputElement>(null);

  // Configurações do Sistema (Aba Configurações)
  const [configTempPath, setConfigTempPath] = useState("");
  const [configJobsPath, setConfigJobsPath] = useState("");
  const [configLogLevel, setConfigLogLevel] = useState("info");
  const [configThreadCount, setConfigThreadCount] = useState(4);
  const [configMemoryStrategy, setConfigMemoryStrategy] = useState("balanced");
  const [configProviders, setConfigProviders] = useState<string[]>([]);
  const [availableProviders, setAvailableProviders] = useState<string[]>(["cpu"]);
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  // Controle de reprodução da mídia de destino para processamento sob demanda
  const [processFromCurrentPoint, setProcessFromCurrentPoint] = useState(false);
  const [targetVideoTime, setTargetVideoTime] = useState(0);

  // Processadores (Aba Criar Novo)
  const [availableProcessors, setAvailableProcessors] = useState<string[]>(["face_swapper"]);
  const [selectedProcessors, setSelectedProcessors] = useState<string[]>(["face_swapper"]);

  // Filtros de Projetos (Aba Projetos)
  const [projectFilter, setProjectFilter] = useState<"all" | "completed" | "processing" | "failed">("all");
  const [jobToDelete, setJobToDelete] = useState<string | null>(null);

  // Efeitos e Handlers do Player / Comparador
  useEffect(() => {
    if (isPlaying) {
      originalVideoRef.current?.play().catch(() => {});
      swappedVideoRef.current?.play().catch(() => {});
    } else {
      originalVideoRef.current?.pause();
      swappedVideoRef.current?.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    if (originalVideoRef.current) originalVideoRef.current.muted = isMuted;
    if (swappedVideoRef.current) swappedVideoRef.current.muted = isMuted;
  }, [isMuted]);

  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    setVideoDuration(0);
  }, [previewOutputUrl]);

  const handleSeek = (time: number) => {
    setCurrentTime(time);
    if (originalVideoRef.current) originalVideoRef.current.currentTime = time;
    if (swappedVideoRef.current) swappedVideoRef.current.currentTime = time;
  };

  const handleTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    const video = e.currentTarget;
    setCurrentTime(video.currentTime);
    
    // Sincronizar o outro vídeo se estiver muito defasado
    const otherVideo = video === swappedVideoRef.current ? originalVideoRef.current : swappedVideoRef.current;
    if (otherVideo && Math.abs(otherVideo.currentTime - video.currentTime) > 0.15) {
      otherVideo.currentTime = video.currentTime;
    }
  };

  const handleLoadedMetadata = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    setVideoDuration(e.currentTarget.duration);
  };

  const handleFullscreen = () => {
    if (videoContainerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      } else {
        videoContainerRef.current.requestFullscreen().catch(() => {});
      }
    }
  };

  // Carregar configuração de API dinâmica ao iniciar
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await fetch("/config.json");
        if (res.ok) {
          const data = await res.json();
          if (data.apiUrl) {
            setApiUrl(data.apiUrl);
          }
        }
      } catch (e) {
        console.warn("Falha ao carregar porta dinâmica, usando padrão 8000:", e);
      } finally {
        setConfigLoaded(true);
      }
    };
    loadConfig();
  }, []);

  // Buscar informações do hardware ao montar
  useEffect(() => {
    if (!configLoaded) return;
    const fetchHardware = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/hardware/devices`);
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
            const resProv = await fetch(`${apiUrl}/api/hardware/providers`);
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
  }, [configLoaded, apiUrl]);

  // Buscar configurações ao montar
  useEffect(() => {
    if (!configLoaded) return;
    const fetchConfig = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/config`);
        if (res.ok) {
          const data = await res.json();
          setConfigTempPath(data.temp_path || "");
          setConfigJobsPath(data.jobs_path || "");
          setConfigLogLevel(data.log_level || "info");
          setConfigThreadCount(data.execution_thread_count || 4);
          setConfigMemoryStrategy(data.video_memory_strategy || "balanced");
          setConfigProviders(data.execution_providers || ["cpu"]);
        }
      } catch (err) {
        console.error("Erro ao buscar configurações:", err);
      }

      try {
        const resProv = await fetch(`${apiUrl}/api/hardware/providers`);
        if (resProv.ok) {
          const providers = await resProv.json();
          if (providers && providers.length > 0) {
            setAvailableProviders(providers);
          }
        }
      } catch (err) {
        console.error("Erro ao buscar provedores disponíveis:", err);
      }
    };
    fetchConfig();
  }, [activeTab, configLoaded, apiUrl]);

  // Buscar processadores disponíveis
  useEffect(() => {
    if (!configLoaded) return;
    const fetchProcessors = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/processors/list`);
        if (res.ok) {
          const data = await res.json();
          setAvailableProcessors(data);
        }
      } catch (e) {
        console.error("Erro ao buscar processadores:", e);
      }
    };
    fetchProcessors();
  }, [configLoaded, apiUrl]);

  // Buscar e atualizar lista de Jobs periodicamente
  const fetchJobs = async () => {
    if (!configLoaded) return;
    try {
      const res = await fetch(`${apiUrl}/api/jobs`);
      if (res.ok) {
        const data = await res.json();
        const mappedJobs = data.map((job: any) => ({
          id: job.id,
          type: "Face Swap",
          status: job.status,
          progress: job.progress,
          time: new Date(job.date_created).toLocaleString(),
          source: job.source ? apiUrl + job.source : undefined,
          target: job.target ? apiUrl + job.target : undefined,
          outputUrl: job.output ? apiUrl + job.output : undefined,
          error_message: job.error_message
        }));
        setJobs(mappedJobs);
        
        const isAnyProcessing = mappedJobs.some((j: any) => j.status === "processing" || j.status === "queued");
        setIsGenerating(isAnyProcessing);
      }
    } catch (err) {
      console.error("Erro ao buscar jobs:", err);
    }
  };

  useEffect(() => {
    if (!configLoaded) return;
    fetchJobs();
    const interval = setInterval(fetchJobs, 2000);
    return () => clearInterval(interval);
  }, [configLoaded, apiUrl]);

  // Pegar o último job completo para exibição no preview
  useEffect(() => {
    const completedJobs = jobs.filter(j => j.status === "completed" && j.outputUrl);
    if (completedJobs.length > 0) {
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
    const res = await fetch(`${apiUrl}/api/media/upload`, {
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
      setSourceImage(apiUrl + data.url);
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
      setTargetVideo(apiUrl + data.url);
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
    
    // Calcular frame de início (estimando 30 FPS se for vídeo)
    const trimFrameStart = processFromCurrentPoint ? Math.round(targetVideoTime * 30) : null;

    try {
      const res = await fetch(`${apiUrl}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_paths: [sourceImageFullPath],
          target_path: targetVideoFullPath,
          face_swapper_weight: faceSwapperWeight,
          face_mask_blur: faceMaskBlur / 50.0,
          detection_threshold: detectionThreshold,
          smoothing: smoothing,
          processors: selectedProcessors,
          output_format: outputFormat.toLowerCase(),
          trim_frame_start: trimFrameStart
        })
      });
      if (!res.ok) {
        throw new Error("Erro ao enviar a tarefa para o servidor.");
      }
      const data = await res.json();
      console.log("Job enviado com sucesso:", data);
      setPreviewOutputUrl(null); // Resetar preview até o novo job terminar
      setActiveTab("create_new"); // Sincroniza redirecionamento
      fetchJobs();
    } catch (err) {
      alert("Falha ao iniciar processamento: " + err);
      setIsGenerating(false);
    }
  };

  // Excluir Job
  const handleDeleteJob = async () => {
    if (!jobToDelete) return;
    const jobId = jobToDelete;
    setJobToDelete(null);
    try {
      const res = await fetch(`${apiUrl}/api/jobs/${jobId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setJobs(prev => prev.filter(j => j.id !== jobId));
      } else {
        const data = await res.json();
        alert("Erro ao excluir: " + (data.detail || "Erro desconhecido"));
      }
    } catch (err) {
      alert("Erro de conexão ao excluir tarefa: " + err);
    }
  };

  // Carregar Job Concluído no Comparador do Dashboard
  const handleLoadToComparator = (job: Job) => {
    if (!job.target || !job.outputUrl) return;
    setTargetVideo(job.target);
    setPreviewOutputUrl(job.outputUrl);
    setActiveTab("create_new");
  };

  // Salvar Configurações
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingConfig(true);
    try {
      const res = await fetch(`${apiUrl}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temp_path: configTempPath || null,
          jobs_path: configJobsPath || null,
          log_level: configLogLevel,
          execution_providers: configProviders,
          execution_thread_count: configThreadCount,
          video_memory_strategy: configMemoryStrategy
        })
      });
      if (res.ok) {
        alert("Configurações salvas com sucesso!");
      } else {
        const data = await res.json();
        alert("Erro ao salvar: " + (data.detail || "Erro desconhecido"));
      }
    } catch (err) {
      alert("Erro de conexão ao salvar configurações: " + err);
    } finally {
      setIsSavingConfig(false);
    }
  };

  const handleExportDiagnostic = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/diagnostic/export`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "facefusion_diagnostic.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert("Erro ao exportar diagnóstico.");
      }
    } catch (err) {
      alert("Erro de conexão ao exportar diagnóstico: " + err);
    }
  };

  // Toggle Processadores Selecionados
  const toggleProcessor = (proc: string) => {
    setSelectedProcessors(prev =>
      prev.includes(proc) ? prev.filter(p => p !== proc) : [...prev, proc]
    );
  };

  // Filtragem dos Jobs para a aba Projetos
  const filteredJobs = jobs.filter(job => {
    if (projectFilter === "all") return true;
    if (projectFilter === "completed") return job.status === "completed";
    if (projectFilter === "failed") return job.status === "failed";
    if (projectFilter === "processing") return job.status === "processing" || job.status === "queued";
    return true;
  });

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
            <button
              onClick={() => setActiveTab("create_new")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "create_new"
                  ? "text-zinc-200 bg-zinc-900/50 border-l-2 border-red-500"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30"
              }`}
            >
              <PlusCircle size={18} className={activeTab === "create_new" ? "text-red-500" : ""} />
              Criar Novo
            </button>
            <button
              onClick={() => setActiveTab("projects")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "projects"
                  ? "text-zinc-200 bg-zinc-900/50 border-l-2 border-red-500"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30"
              }`}
            >
              <FolderOpen size={18} className={activeTab === "projects" ? "text-red-500" : ""} />
              Projetos
            </button>
            <button
              onClick={() => setActiveTab("settings")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "settings"
                  ? "text-zinc-200 bg-zinc-900/50 border-l-2 border-red-500"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/30"
              }`}
            >
              <Settings size={18} className={activeTab === "settings" ? "text-red-500" : ""} />
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

      {/* 2. Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        


        {/* Workspace Body */}
        <div className="flex-1 p-4 md:p-6 flex flex-col overflow-hidden">

          {/* =          {/* ABA 1: CRIAR NOVO */}
          {activeTab === "create_new" && (
            <div className="flex-1 flex flex-col overflow-hidden space-y-4">


              {/* Seção 2: Área de Mídia (Upload) e Controles */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 overflow-hidden">
                
                {/* Esquerda: Upload e Configuração */}
                <div className="space-y-4 flex flex-col overflow-hidden h-full">
                  
                  {/* Media Inputs Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-[1.1] min-h-[160px]">
                    {/* Source Image */}
                    <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 flex flex-col justify-between h-full">
                      <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Imagem de Origem (Source)</span>
                      <input
                        type="file"
                        ref={sourceInputRef}
                        accept="image/*"
                        className="hidden"
                        onChange={handleSourceUpload}
                      />
                      {sourceImage ? (
                        <div className="relative flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex items-center justify-center group">
                          <img src={sourceImage} alt="Source Face" className="object-contain w-full h-full" />
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
                          className="border border-dashed border-zinc-800 rounded-lg flex-1 w-full flex flex-col items-center justify-center p-2 hover:border-red-500/40 hover:bg-red-500/5 transition-all group cursor-pointer text-center"
                        >
                          <Upload size={24} className="text-zinc-600 group-hover:text-red-500 mb-2 transition-all" />
                          <p className="text-xs text-zinc-400 font-semibold">Arraste a foto da face</p>
                          <span className="text-[10px] text-zinc-500">ou clique para buscar</span>
                        </div>
                      )}
                    </div>

                    {/* Target Media */}
                    <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 flex flex-col justify-between h-full">
                      <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider block mb-2">Mídia de Destino (Target)</span>
                      <input
                        type="file"
                        ref={targetInputRef}
                        accept="image/*,video/*"
                        className="hidden"
                        onChange={handleTargetUpload}
                      />
                      {targetVideo ? (
                        <div className="relative flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex flex-col justify-between group">
                          {targetVideo.match(/\.(mp4|webm|mkv|avi|mov)$/i) ? (
                            <div className="relative w-full h-full flex flex-col justify-between">
                              <video 
                                src={targetVideo} 
                                className="object-contain w-full h-[75%] bg-black" 
                                controls 
                                onTimeUpdate={(e) => setTargetVideoTime(e.currentTarget.currentTime)}
                              />
                              <div className="p-2 bg-zinc-950/80 flex items-center gap-2 border-t border-zinc-850 h-[25%]">
                                <input
                                  type="checkbox"
                                  id="trim-start-check-dash"
                                  checked={processFromCurrentPoint}
                                  onChange={(e) => setProcessFromCurrentPoint(e.target.checked)}
                                  className="w-3.5 h-3.5 accent-red-600 rounded cursor-pointer"
                                />
                                <label htmlFor="trim-start-check-dash" className="text-[9px] text-zinc-300 select-none cursor-pointer truncate">
                                  Processar a partir deste ponto ({targetVideoTime.toFixed(1)}s)
                                </label>
                              </div>
                            </div>
                          ) : (
                            <img src={targetVideo} alt="Target Media" className="object-contain w-full h-full" />
                          )}
                          <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setTargetVideo(null);
                                setTargetVideoFullPath(null);
                                setTargetVideoName("");
                            }}
                            className="absolute top-3 right-3 z-30 bg-red-600/90 hover:bg-red-500 text-white p-2 rounded-lg shadow-lg hover:scale-105 active:scale-95 transition-all opacity-0 group-hover:opacity-100 cursor-pointer flex items-center justify-center border border-red-500/20"
                            title="Substituir mídia de destino"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ) : (
                        <div 
                          onClick={() => targetInputRef.current?.click()}
                          className="border border-dashed border-zinc-800 rounded-lg flex-1 w-full flex flex-col items-center justify-center p-2 hover:border-red-500/40 hover:bg-red-500/5 transition-all group cursor-pointer text-center"
                        >
                          <Upload size={24} className="text-zinc-600 group-hover:text-red-500 mb-2 transition-all" />
                          <p className="text-xs text-zinc-400 font-semibold">Arraste imagem ou vídeo</p>
                          <span className="text-[10px] text-zinc-500">ou clique para buscar</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Processadores de Frame */}
                  <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 flex flex-col flex-[0.8] min-h-[100px] overflow-hidden">
                    <div className="flex items-center gap-2 text-white font-bold border-b border-zinc-900 pb-1.5 mb-2">
                      <Cpu size={14} className="text-red-500" />
                      <h3 className="text-xs">Processadores de Frame</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-2 flex-1 overflow-y-auto pr-1">
                      {availableProcessors.map(proc => (
                        <button
                          key={proc}
                          type="button"
                          onClick={() => toggleProcessor(proc)}
                          className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-semibold transition-all ${
                            selectedProcessors.includes(proc)
                              ? "bg-red-500/10 border-red-500/40 text-red-400"
                              : "bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                          }`}
                        >
                          <span className="truncate">{proc.replace("_", " ").toUpperCase()}</span>
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ml-2 ${selectedProcessors.includes(proc) ? "bg-red-500" : "bg-zinc-700"}`} />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Parâmetros e Sliders */}
                  <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 flex flex-col flex-[1.1] min-h-[140px] justify-center">
                    <div className="flex items-center gap-2 text-white font-bold border-b border-zinc-900 pb-1.5 mb-3">
                      <Sliders size={14} className="text-red-500" />
                      <h3 className="text-xs">Ajustes Técnicos do Processador</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 flex-1 justify-center">
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-zinc-300">Face Swapper Weight</span>
                          <span className="text-red-500 font-mono">{faceSwapperWeight.toFixed(2)}</span>
                        </div>
                        <input
                          type="range" min="0" max="1" step="0.05"
                          value={faceSwapperWeight}
                          onChange={e => setFaceSwapperWeight(parseFloat(e.target.value))}
                          className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-zinc-300">Face Mask Blur</span>
                          <span className="text-red-500 font-mono">{faceMaskBlur}px</span>
                        </div>
                        <input
                          type="range" min="0" max="50" step="1"
                          value={faceMaskBlur}
                          onChange={e => setFaceMaskBlur(parseInt(e.target.value))}
                          className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-zinc-300">Limiar de Detecção</span>
                          <span className="text-red-500 font-mono">{detectionThreshold.toFixed(2)}</span>
                        </div>
                        <input
                          type="range" min="0" max="1" step="0.05"
                          value={detectionThreshold}
                          onChange={e => setDetectionThreshold(parseFloat(e.target.value))}
                          className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-zinc-300">Suavização (Smoothing)</span>
                          <span className="text-red-500 font-mono">{smoothing}px</span>
                        </div>
                        <input
                          type="range" min="0" max="20" step="1"
                          value={smoothing}
                          onChange={e => setSmoothing(parseInt(e.target.value))}
                          className="w-full accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Direita: Preview Compartivo */}
                <div className="space-y-4 flex flex-col overflow-hidden h-full">
                  <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 flex-1 flex flex-col justify-between overflow-hidden">
                    <div className="flex items-center justify-between text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2">
                      <span>Visualização de Resultado</span>
                      <span className="text-[10px] bg-red-600/10 text-red-500 border border-red-500/20 px-2 py-0.5 rounded font-bold">1080p</span>
                    </div>

                    <div 
                      ref={videoContainerRef}
                      className="relative flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden select-none min-h-[200px]"
                      onMouseDown={(e) => {
                        if (previewOutputUrl && targetVideo) {
                          setIsSliding(true);
                          handleSliderMove(e.clientX);
                        }
                      }}
                      onTouchStart={(e) => {
                        if (previewOutputUrl && targetVideo) {
                          setIsSliding(true);
                          handleSliderMove(e.touches[0].clientX);
                        }
                      }}
                    >
                      {/* Imagem/Vídeo com Comparador Deslizante (Antes/Depois) */}
                      {previewOutputUrl ? (
                        targetVideo ? (
                          <div className="absolute inset-0 w-full h-full flex items-center justify-center">
                            {/* Camada de Baixo: Target original ("Antes") */}
                            {targetVideo.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                              <video 
                                ref={originalVideoRef}
                                src={targetVideo} 
                                className="absolute inset-0 object-contain w-full h-full pointer-events-none" 
                                muted 
                                loop 
                                playsInline
                              />
                            ) : (
                              <img 
                                src={targetVideo} 
                                alt="Original Target" 
                                className="absolute inset-0 object-contain w-full h-full pointer-events-none" 
                              />
                            )}

                            {/* Camada de Cima: Swapped result ("Depois") com recorte de clipPath */}
                            {previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                              <video 
                                ref={swappedVideoRef}
                                src={previewOutputUrl} 
                                className="absolute inset-0 object-contain w-full h-full pointer-events-none" 
                                muted 
                                loop 
                                playsInline
                                onTimeUpdate={handleTimeUpdate}
                                onLoadedMetadata={handleLoadedMetadata}
                                style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
                              />
                            ) : (
                              <img 
                                src={previewOutputUrl} 
                                alt="Swapped Output" 
                                className="absolute inset-0 object-contain w-full h-full pointer-events-none" 
                                style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
                              />
                            )}

                            {/* Linha Divisória Vertical e Cursor Handle */}
                            <div 
                              className="absolute top-0 bottom-0 w-[2px] bg-red-500 z-30 pointer-events-none"
                              style={{ left: `${sliderPosition}%` }}
                            >
                              <div 
                                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white text-zinc-950 flex items-center justify-center shadow-lg border border-red-500 hover:scale-110 active:scale-95 transition-transform select-none pointer-events-auto cursor-ew-resize font-bold text-sm"
                              >
                                ↔
                              </div>
                            </div>

                            {/* Labels Visuais */}
                            <div className="absolute top-3 left-3 bg-black/60 border border-zinc-800 px-2 py-0.5 rounded text-[9px] font-extrabold text-red-500 uppercase tracking-wider select-none z-20">
                              Swapped
                            </div>
                            <div className="absolute top-3 right-3 bg-black/60 border border-zinc-800 px-2 py-0.5 rounded text-[9px] font-extrabold text-zinc-400 uppercase tracking-wider select-none z-20">
                              Original
                            </div>
                          </div>
                        ) : (
                          // Fallback se não houver targetVideo em memória
                          previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                            <video 
                              ref={swappedVideoRef}
                              src={previewOutputUrl} 
                              className="absolute inset-0 object-contain w-full h-full pointer-events-none" 
                              muted 
                              loop 
                              playsInline
                              autoPlay
                              onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                              onLoadedMetadata={(e) => setVideoDuration(e.currentTarget.duration)}
                            />
                          ) : (
                            <img src={previewOutputUrl} alt="Swapped Face" className="absolute inset-0 object-contain w-full h-full pointer-events-none" />
                          )
                        )
                      ) : (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 gap-2 p-4">
                          <ImageIcon size={32} className="text-zinc-700" />
                          <span className="text-xs font-semibold text-zinc-400">Sem Visualização de Saída</span>
                          <span className="text-[10px] text-zinc-600 text-center max-w-[220px]">
                            Selecione a origem/destino e inicie o processamento para ver o resultado aqui.
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-4 bg-zinc-950/55 border border-zinc-900 rounded-lg p-2.5 mt-2">
                      <button 
                        onClick={() => setIsPlaying(!isPlaying)} 
                        disabled={!previewOutputUrl || !previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i)}
                        className="text-zinc-200 hover:text-red-500 transition-colors disabled:text-zinc-700 disabled:cursor-not-allowed cursor-pointer"
                      >
                        {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                      </button>
                      
                      <input
                        type="range"
                        min={0}
                        max={videoDuration || 100}
                        step={0.1}
                        value={currentTime}
                        disabled={!previewOutputUrl || !previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i)}
                        onChange={(e) => handleSeek(parseFloat(e.target.value))}
                        className="flex-1 accent-red-600 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                      />

                      <span className="text-[10px] text-zinc-500 font-mono select-none">
                        {formatTime(currentTime)} / {formatTime(videoDuration)}
                      </span>
                      
                      <button 
                        onClick={() => setIsMuted(!isMuted)}
                        disabled={!previewOutputUrl || !previewOutputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i)}
                        className="text-zinc-400 hover:text-zinc-200 transition-colors disabled:text-zinc-700 disabled:cursor-not-allowed cursor-pointer"
                        title={isMuted ? "Unmute" : "Mute"}
                      >
                        {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
                      </button>
                      
                      <button 
                        onClick={handleFullscreen}
                        disabled={!previewOutputUrl}
                        className="text-zinc-400 hover:text-zinc-200 transition-colors disabled:text-zinc-700 disabled:cursor-not-allowed cursor-pointer"
                        title="Tela Cheia"
                      >
                        <Maximize2 size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end flex-shrink-0">
                    <div className="bg-zinc-950/30 border border-zinc-900 rounded-xl p-4 space-y-2">
                      <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block">Opções de Exportação</span>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="text-[10px] text-zinc-500 block mb-1">Formato</label>
                          <div className="relative">
                            <select value={outputFormat} onChange={e => setOutputFormat(e.target.value)} className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer">
                              <option>MP4</option><option>WEBM</option><option>MKV</option>
                            </select>
                            <ChevronDown size={12} className="absolute right-2 top-2.5 text-zinc-500 pointer-events-none" />
                          </div>
                        </div>
                        <div>
                          <label className="text-[10px] text-zinc-500 block mb-1">Qualidade</label>
                          <div className="relative">
                            <select value={outputQuality} onChange={e => setOutputQuality(e.target.value)} className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer">
                              <option>High</option><option>Medium</option><option>Low</option>
                            </select>
                            <ChevronDown size={12} className="absolute right-2 top-2.5 text-zinc-500 pointer-events-none" />
                          </div>
                        </div>
                        <div>
                          <label className="text-[10px] text-zinc-500 block mb-1">Resolução</label>
                          <div className="relative">
                            <select value={outputResolution} onChange={e => setOutputResolution(e.target.value)} className="w-full bg-zinc-900 border border-zinc-800 text-xs px-2.5 py-1.5 rounded appearance-none font-bold text-zinc-200 outline-none cursor-pointer">
                              <option>1080p</option><option>720p</option><option>4K</option>
                            </select>
                            <ChevronDown size={12} className="absolute right-2 top-2.5 text-zinc-500 pointer-events-none" />
                          </div>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={handleGenerateSwap}
                      disabled={isGenerating}
                      className={`w-full h-12 font-extrabold rounded-xl flex items-center justify-center gap-2 text-white shadow-lg transition-all ${
                        isGenerating
                          ? "bg-zinc-800 border border-zinc-700 cursor-not-allowed text-zinc-500"
                          : "bg-red-600 hover:bg-red-500 hover:scale-[1.02] active:scale-[0.98] shadow-red-600/20 cursor-pointer"
                      }`}
                    >
                      {isGenerating ? (
                        <><RefreshCw size={18} className="animate-spin text-zinc-500" />PROCESSANDO...</>
                      ) : (
                        "INICIAR PROCESSAMENTO (SWAP)"
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ABA 3: PROJETOS (GALERIA) */}
          {activeTab === "projects" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
                <div className="flex items-center gap-3">
                  <FolderOpen className="text-red-500" size={24} />
                  <div>
                    <h2 className="text-xl font-bold text-white">Galeria de Projetos</h2>
                    <p className="text-xs text-zinc-500">Histórico de todas as manipulações criadas e seus arquivos.</p>
                  </div>
                </div>

                {/* Filtros */}
                <div className="flex items-center gap-2 bg-zinc-900/50 p-1 border border-zinc-800 rounded-lg">
                  <button
                    onClick={() => setProjectFilter("all")}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${projectFilter === "all" ? "bg-red-600 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
                  >
                    Todos
                  </button>
                  <button
                    onClick={() => setProjectFilter("completed")}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${projectFilter === "completed" ? "bg-red-600 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
                  >
                    Concluídos
                  </button>
                  <button
                    onClick={() => setProjectFilter("processing")}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${projectFilter === "processing" ? "bg-red-600 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
                  >
                    Ativos
                  </button>
                  <button
                    onClick={() => setProjectFilter("failed")}
                    className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${projectFilter === "failed" ? "bg-red-600 text-white" : "text-zinc-400 hover:text-zinc-200"}`}
                  >
                    Falhas
                  </button>
                </div>
              </div>

              {/* Grid de Projetos com limite de 2 linhas e rolagem vertical */}
              <div className="max-h-[790px] overflow-y-auto pr-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {filteredJobs.map(job => (
                    <div key={job.id} className="bg-zinc-950/40 border border-zinc-900 rounded-xl overflow-hidden flex flex-col justify-between group">
                      {/* Preview Media */}
                      <div className="aspect-[16/10] bg-zinc-900/60 flex items-center justify-center border-b border-zinc-900 relative">
                        {job.status === "completed" && job.outputUrl ? (
                          job.outputUrl.match(/\.(mp4|webm|mkv|avi|mov)/i) ? (
                            <video src={job.outputUrl} className="w-full h-full object-cover" muted loop autoPlay />
                          ) : (
                            <img src={job.outputUrl} alt="Output" className="w-full h-full object-cover" />
                          )
                        ) : job.status === "failed" ? (
                          <div className="flex flex-col items-center gap-2 p-4 text-center">
                            <AlertCircle size={32} className="text-red-500" />
                            <span className="text-xs font-bold text-zinc-400">Falha no Processamento</span>
                            <div className="max-h-[80px] overflow-y-auto text-[10px] text-zinc-600 bg-black/40 p-2 rounded max-w-[200px] break-all border border-zinc-900 font-mono">
                              {job.error_message || "Erro desconhecido durante execução."}
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center gap-2 text-zinc-500">
                            <RefreshCw size={32} className="animate-spin text-amber-500" />
                            <span className="text-xs font-bold">Processando ({job.progress}%)</span>
                          </div>
                        )}

                        {/* Status Overlay Badge */}
                        <div className="absolute top-3 right-3">
                          {job.status === "completed" ? (
                            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-extrabold uppercase">Concluído</span>
                          ) : job.status === "failed" ? (
                            <span className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded font-extrabold uppercase">Falhou</span>
                          ) : (
                            <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded font-extrabold uppercase animate-pulse">Ativo</span>
                          )}
                        </div>
                      </div>

                      {/* Card Details */}
                      <div className="p-5 space-y-4">
                        <div>
                          <div className="flex justify-between items-start">
                            <h3 className="font-bold text-sm text-white truncate max-w-[150px]">{job.id}</h3>
                            <span className="text-[10px] text-zinc-500 font-semibold">{job.time}</span>
                          </div>
                          <p className="text-xs text-zinc-400">Face Swap Pipeline</p>
                        </div>

                        {/* Ações */}
                        <div className="flex items-center gap-2 border-t border-zinc-900 pt-4">
                          {job.status === "completed" && (
                            <>
                              <button
                                onClick={() => handleLoadToComparator(job)}
                                className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs py-2 rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 border border-zinc-800"
                              >
                                <ExternalLink size={12} /> Comparar
                              </button>
                              <a
                                href={job.outputUrl}
                                download={`faceswap-${job.id}`}
                                className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs p-2 rounded-lg font-bold transition-all border border-zinc-800 flex items-center justify-center"
                                title="Baixar Mídia de Saída"
                              >
                                <Download size={14} />
                              </a>
                            </>
                          )}
                          <button
                            onClick={() => setJobToDelete(job.id)}
                            className="bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-500 text-xs p-2 rounded-lg font-bold transition-all flex items-center justify-center"
                            title="Excluir Tarefa"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {filteredJobs.length === 0 && (
                <div className="bg-zinc-950/20 border border-zinc-900 rounded-xl p-12 text-center text-zinc-500 max-w-md mx-auto">
                  Nenhum projeto encontrado para o filtro selecionado.
                </div>
              )}
            </div>
          )}

          {/* ABA 4: CONFIGURAÇÕES */}
          {activeTab === "settings" && (
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="flex items-center gap-3 border-b border-zinc-900 pb-4">
                <Settings className="text-red-500" size={24} />
                <div>
                  <h2 className="text-xl font-bold text-white">Configurações do Sistema</h2>
                  <p className="text-xs text-zinc-500">Gerencie diretórios, níveis de log e parâmetros de aceleração de hardware.</p>
                </div>
              </div>

              <form onSubmit={handleSaveConfig} className="bg-zinc-950/40 border border-zinc-900 rounded-xl p-6 space-y-6">
                
                {/* Diretórios */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Folder size={16} className="text-red-500" /> Diretórios do Sistema
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs text-zinc-400 font-semibold">Caminho Temporário (Temp Path)</label>
                      <input
                        type="text"
                        value={configTempPath}
                        onChange={e => setConfigTempPath(e.target.value)}
                        placeholder="Ex: .temp"
                        className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500 transition-colors"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-zinc-400 font-semibold">Pasta de Tarefas (Jobs Path)</label>
                      <input
                        type="text"
                        value={configJobsPath}
                        onChange={e => setConfigJobsPath(e.target.value)}
                        placeholder="Ex: .jobs"
                        className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500 transition-colors"
                      />
                    </div>
                  </div>
                </div>

                {/* Aceleração de Hardware */}
                <div className="space-y-4 border-t border-zinc-900 pt-6">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Cpu size={16} className="text-red-500" /> Aceleração e Performance
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs text-zinc-400 font-semibold font-sans">Estratégia de Memória do Vídeo</label>
                      <select
                        value={configMemoryStrategy}
                        onChange={e => setConfigMemoryStrategy(e.target.value)}
                        className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500 transition-colors cursor-pointer"
                      >
                        <option value="strict">Strict (Baixo Uso)</option>
                        <option value="balanced">Balanced (Equilibrado)</option>
                        <option value="tolerant">Tolerant (Desempenho Máximo)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs text-zinc-400 font-semibold">Quantidade de Threads</label>
                      <input
                        type="number"
                        min="1"
                        max="32"
                        value={configThreadCount}
                        onChange={e => setConfigThreadCount(parseInt(e.target.value) || 1)}
                        className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500 transition-colors"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs text-zinc-400 font-semibold block">Provedores de Execução Disponíveis</label>
                    <div className="flex flex-wrap gap-2">
                      {availableProviders.map(prov => {
                        const isSelected = configProviders.includes(prov);
                        return (
                          <button
                            key={prov}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                if (configProviders.length > 1) {
                                  setConfigProviders(configProviders.filter(p => p !== prov));
                                }
                              } else {
                                setConfigProviders([...configProviders, prov]);
                              }
                            }}
                            className={`px-3 py-1.5 rounded text-xs font-bold uppercase flex items-center gap-1.5 border transition-all cursor-pointer ${
                              isSelected
                                ? "bg-red-500/20 border-red-500/40 text-red-400"
                                : "bg-zinc-900/60 border-zinc-800 text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"
                            }`}
                          >
                            {isSelected && <CheckCircle size={10} />}
                            {prov}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Sistema Geral */}
                <div className="space-y-4 border-t border-zinc-900 pt-6">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Terminal size={16} className="text-red-500" />Logs e Monitoramento
                  </h3>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400 font-semibold">Nível de Log (Log Level)</label>
                    <select
                      value={configLogLevel}
                      onChange={e => setConfigLogLevel(e.target.value)}
                      className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-300 outline-none focus:border-red-500 transition-colors cursor-pointer"
                    >
                      <option value="error">Error</option>
                      <option value="warning">Warning</option>
                      <option value="info">Info</option>
                      <option value="debug">Debug</option>
                    </select>
                  </div>
                </div>

                <div className="border-t border-zinc-900 pt-6 flex justify-between items-center">
                  <button
                    type="button"
                    onClick={handleExportDiagnostic}
                    className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 font-bold px-6 py-2.5 rounded-lg text-xs transition-all border border-zinc-800 flex items-center gap-2 cursor-pointer"
                  >
                    <Download size={14} />
                    EXPORTAR DIAGNÓSTICO
                  </button>

                  <button
                    type="submit"
                    disabled={isSavingConfig}
                    className="bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-2.5 rounded-lg text-xs transition-all shadow-lg shadow-red-600/20 flex items-center gap-2 cursor-pointer disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed"
                  >
                    {isSavingConfig ? <RefreshCw size={14} className="animate-spin" /> : null}
                    SALVAR CONFIGURAÇÕES
                  </button>
                </div>
              </form>
            </div>
          )}

        </div>
      </main>

      {/* Modal de Confirmação de Exclusão */}
      {jobToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-900 rounded-2xl p-6 w-full max-w-md shadow-2xl shadow-black/80 animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-base font-bold text-white mb-2">Confirmar Exclusão</h3>
            <p className="text-xs text-zinc-400 mb-6 leading-relaxed">
              Deseja realmente excluir a tarefa <span className="text-red-500 font-mono font-bold">{jobToDelete}</span>? Esta ação é irreversível e removerá todos os arquivos e mídias associados.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setJobToDelete(null)}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-zinc-900 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 transition-all cursor-pointer"
              >
                Cancelar
              </button>
              <button
                onClick={handleDeleteJob}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/20 transition-all cursor-pointer"
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
