"use client";

import { useState } from "react";
import { HeaderBar } from "@/components/HeaderBar";
import { UploadPanel } from "@/components/UploadPanel";
import { LoadingPipeline } from "@/components/LoadingPipeline";
import { OverviewCards, ClusterList, KnowledgePanel, AIReasoningRightColumn, ServiceBreakdownChart } from "@/components/ResultPanels";
import { AnalyzeResponse, AnalysisResult } from "@/types/schema";

const PIPELINE_STEPS = [
  { id: "read", label: "Đang đọc file log..." },
  { id: "cluster", label: "Đang phân cụm lỗi bằng AI..." },
  { id: "rag", label: "Đang truy xuất KB (RAG)..." },
  { id: "plan", label: "Đang tạo kế hoạch kiểm tra..." },
  { id: "tool", label: "Đang thực thi công cụ thật..." },
  { id: "conclude", label: "Đang tổng hợp kết luận cuối..." },
];

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"idle" | "analyzing" | "completed" | "error">("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeStep, setActiveStep] = useState(0);

  const handleAnalyze = async () => {
    if (!file) return;
    setStatus("analyzing");
    setResult(null);
    setActiveStep(0);

    // Simulate pipeline steps for UI effect (actual call is one-shot)
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev < 5 ? prev + 1 : prev));
    }, 2500);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_query", query);

      const res = await fetch("http://127.0.0.1:8000/analyze-log", {
        method: "POST",
        body: formData,
      });

      clearInterval(timer);
      setActiveStep(6); // All done

      if (!res.ok) throw new Error("Lỗi gọi API");

      const data: AnalyzeResponse = await res.json();
      if (data.success && data.result) {
        setResult(data.result);
        setStatus("completed");
      } else {
        throw new Error("API trả về lỗi hoặc thiếu dữ liệu");
      }
    } catch (err) {
      clearInterval(timer);
      console.error(err);
      setStatus("error");
    }
  };

  const currentSteps = PIPELINE_STEPS.map((s, i) => ({
    ...s,
    active: i === activeStep,
    completed: i < activeStep || status === "completed",
  }));

  return (
    <div className="flex flex-col min-h-screen">
      <HeaderBar status={status} onReset={() => { setStatus("idle"); setResult(null); setFile(null); setActiveStep(0); }} />
      
      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        {status === "idle" || status === "error" ? (
          <div className="max-w-4xl mx-auto mt-12">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-slate-100 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">Điều Tra Sự Cố Thông Minh</h2>
              <p className="text-slate-400">Trợ lý phân tích tự động tìm kiếm gốc rễ lỗi Apache bằng AI, kết hợp RAG và Function Calling.</p>
            </div>
            <UploadPanel 
              file={file} setFile={setFile} 
              query={query} setQuery={setQuery} 
              onAnalyze={handleAnalyze} isAnalyzing={status === "analyzing"} 
            />
            {status === "error" && (
              <div className="mt-8 p-4 bg-rose-500/10 border border-rose-500/50 rounded-xl text-rose-400 text-center">
                Đã có lỗi xảy ra khi gọi backend API. Vui lòng kiểm tra server FastAPI.
              </div>
            )}
          </div>
        ) : null}

        {status === "analyzing" && (
          <LoadingPipeline steps={currentSteps} />
        )}

        {status === "completed" && result && (
          <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
            <OverviewCards result={result} />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Column (60%) */}
              <div className="lg:col-span-7 space-y-8">
                <ServiceBreakdownChart topServices={result.overview.top_services} />
                <ClusterList clusters={result.clusters} />
                <KnowledgePanel docs={result.retrieved_knowledge} />
              </div>

              {/* Right Column (40%) */}
              <div className="lg:col-span-5">
                <AIReasoningRightColumn result={result} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
