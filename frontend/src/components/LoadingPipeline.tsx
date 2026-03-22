import { CheckCircle2, Loader2, Circle } from "lucide-react";

interface LoadingPipelineProps {
  steps: { id: string; label: string; active: boolean; completed: boolean }[];
}

export function LoadingPipeline({ steps }: LoadingPipelineProps) {
  return (
    <div className="w-full max-w-3xl mx-auto my-12 p-8 bg-slate-800/20 rounded-2xl border border-slate-700/50 backdrop-blur-sm shadow-2xl">
      <h3 className="text-lg font-medium text-slate-200 mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-slate-200 to-slate-400">
        AI Investigation Pipeline
      </h3>
      <div className="flex flex-col gap-6 relative">
        <div className="absolute left-4 top-4 bottom-4 w-px bg-slate-700/50 z-0"></div>
        {steps.map((step, idx) => (
          <div key={step.id} className="flex items-center gap-6 relative z-10">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border-2 transition-all duration-500
                ${
                  step.completed
                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                    : step.active
                    ? "bg-blue-500/20 border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
                    : "bg-slate-800 border-slate-600 text-slate-500"
                }
              `}
            >
              {step.completed ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : step.active ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Circle className="w-3 h-3 fill-current" />
              )}
            </div>
            <div className={`flex-1 transition-all duration-500 ${step.active ? "opacity-100" : "opacity-50"}`}>
              <p
                className={`font-medium text-lg ${
                  step.completed ? "text-emerald-400" : step.active ? "text-blue-400" : "text-slate-400"
                }`}
              >
                {step.label}
              </p>
              {step.active && (
                <p className="text-sm text-slate-400 mt-1 animate-pulse">
                  Hệ thống đang xử lý dữ liệu ở giai đoạn này...
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
