import { Search, Activity, ShieldAlert, CheckCircle2 } from "lucide-react";

interface HeaderBarProps {
  status: "idle" | "analyzing" | "completed" | "error";
  onReset: () => void;
}

export function HeaderBar({ status, onReset }: HeaderBarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20">
            <Search className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="font-semibold text-lg bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              AI Log Analyzer
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">Trợ lý điều tra log Apache</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {status === "idle" && (
            <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700/50">
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse"></span>
              Sẵn sàng
            </div>
          )}
          {status === "analyzing" && (
            <div className="flex items-center gap-2 text-sm text-blue-400 bg-blue-500/10 px-3 py-1.5 rounded-full border border-blue-500/20">
              <Activity className="w-4 h-4 animate-spin" />
              Đang phân tích...
            </div>
          )}
          {status === "completed" && (
            <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4" />
              Hoàn tất
            </div>
          )}
          {status === "error" && (
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 px-3 py-1.5 rounded-full border border-red-500/20">
              <ShieldAlert className="w-4 h-4" />
              Lỗi
            </div>
          )}

          {status === "completed" && (
            <button
              onClick={onReset}
              className="text-sm px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors border border-slate-700"
            >
              Phân tích lại
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
