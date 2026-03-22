import { AnalysisResult, ErrorCluster, ActionCheck, ToolExecutionResult } from "@/types/schema";
import { AlertTriangle, ServerCrash, FileCode, Search, CheckCircle2, ShieldAlert, Cpu, Terminal, BookOpen, ScrollText, Activity } from "lucide-react";

export function OverviewCards({ result }: { result: AnalysisResult }) {
  const isHigh = result.severity === "CRITICAL" || result.severity === "HIGH";
  const isLow = result.severity === "LOW";
  const sevColor = isHigh ? "text-red-400 bg-red-500/10 border-red-500/20" : isLow ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : "text-yellow-400 bg-yellow-500/10 border-yellow-500/20";

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 flex flex-col items-center justify-center text-center">
        <p className="text-sm text-slate-400 mb-1">Tổng Số Log</p>
        <p className="text-2xl font-semibold text-slate-200">{result.overview.total_lines.toLocaleString()}</p>
      </div>
      <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 flex flex-col items-center justify-center text-center">
        <p className="text-sm text-slate-400 mb-1">Số Lỗi Parse</p>
        <p className={`text-2xl font-semibold ${result.overview.failed_lines > 0 ? "text-orange-400" : "text-slate-200"}`}>{result.overview.failed_lines}</p>
      </div>
      <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 flex flex-col items-center justify-center text-center">
        <p className="text-sm text-slate-400 mb-1">Mã Lỗi Phát Hiện</p>
        <p className="text-2xl font-semibold text-rose-400">{result.overview.error_count}</p>
      </div>
      <div className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${sevColor}`}>
        <p className="text-sm text-current/80 mb-1">Mức Độ</p>
        <p className="text-2xl font-bold font-mono tracking-wider">{result.severity}</p>
      </div>
      <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20 flex flex-col items-center justify-center text-center">
        <p className="text-sm text-blue-300/80 mb-1">Số Cụm Vấn Đề</p>
        <p className="text-2xl font-semibold text-blue-400">{result.clusters.length}</p>
      </div>
    </div>
  );
}

export function ClusterList({ clusters }: { clusters: ErrorCluster[] }) {
  if (!clusters?.length) return <p className="text-sm text-slate-500">Chưa có dữ liệu phân cụm.</p>;
  return (
    <div className="space-y-4">
      <h3 className="flex items-center gap-2 font-medium text-lg text-slate-200 border-b border-slate-800 pb-2"><ServerCrash className="w-5 h-5 text-rose-400"/> Các Cụm Lỗi Phát Hiện</h3>
      <div className="space-y-3">
        {clusters.map((c, i) => (
          <div key={i} className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl hover:border-slate-600 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium text-slate-200 break-words">{c.label}</h4>
              <span className="text-xs font-mono font-medium text-rose-400 bg-rose-500/10 px-2 py-1 rounded bg-slate-900 border border-rose-500/20 whitespace-nowrap">{c.count} lần</span>
            </div>
            <div className="flex gap-2 text-xs text-slate-400 mb-3">
              <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">Services: {c.services.join(", ")}</span>
              {i === 0 && <span className="bg-blue-500/10 text-blue-400 px-2 py-1 rounded border border-blue-500/30 font-medium">Issue Chính</span>}
            </div>
            <div className="space-y-1">
              {c.samples.map((s, idx) => (
                <div key={idx} className="font-mono text-[11px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800/50 overflow-x-auto whitespace-pre">
                  {s}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function KnowledgePanel({ docs }: { docs: string[] }) {
  if (!docs?.length) return null;
  return (
    <div className="space-y-4 mt-8">
      <h3 className="flex items-center gap-2 font-medium text-lg text-slate-200 border-b border-slate-800 pb-2"><BookOpen className="w-5 h-5 text-indigo-400"/> Tri thức truy xuất (RAG)</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {docs.map((d, i) => {
          const match = d.match(/^\[(.*?)\]\s([\s\S]*)$/);
          const metaStr = match ? match[1] : "";
          const content = match ? match[2] : d;
          
          let source = "Unknown", type = "";
          metaStr.split(",").forEach(part => {
            const [k, v] = part.split("=").map(x => x.trim());
            if(k==="source") source = v;
            if(k==="type") type = v;
          });

          return (
            <div key={i} className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl hover:bg-indigo-500/10 transition-colors flex flex-col h-full">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-indigo-300 truncate max-w-[70%]">{source}</span>
                {type && <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{type}</span>}
              </div>
              <div className="font-mono text-xs text-slate-400 flex-1 overflow-hidden relative">
                 <div className="line-clamp-4">{content}</div>
                 <div className="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-slate-900/50 to-transparent"></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function AIReasoningRightColumn({ result }: { result: AnalysisResult }) {
  return (
    <div className="space-y-8">
      {/* Before / After Concept */}
      <div className="p-6 bg-slate-800/40 border border-slate-700/50 rounded-2xl shadow-xl">
        <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400"/> Đánh giá ban đầu (Trước khi dùng tool)
        </h3>
        <p className="text-sm text-slate-300 leading-relaxed mb-6 bg-slate-900/50 p-4 rounded-xl border border-slate-800">{result.summary}</p>
        
        <div className="grid grid-cols-1 gap-6">
          <div>
             <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2"><Search className="w-4 h-4 text-orange-400"/> Nguyên nhân khả dĩ</h4>
             <ul className="space-y-2">
               {result.probable_causes.map((c, i) => (
                 <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                   <span className="w-5 h-5 text-xs flex items-center justify-center bg-slate-800 rounded-full shrink-0 text-slate-400">{i+1}</span>
                   <span className="mt-0.5">{c}</span>
                 </li>
               ))}
             </ul>
          </div>
          <div>
             <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-400"/> Hành động đề xuất</h4>
             <ul className="space-y-2">
               {result.recommendations.map((c, i) => (
                 <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                   <span className="w-1.5 h-1.5 rounded-full bg-slate-600 mt-1.5 shrink-0"></span>
                   <span>{c}</span>
                 </li>
               ))}
             </ul>
          </div>
        </div>
      </div>

      <div className="p-6 bg-slate-800/40 border border-blue-500/20 rounded-2xl shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 bg-blue-500 h-full"></div>
        <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-blue-400"/> Function Calling & Result
        </h3>
        <p className="text-xs text-slate-400 mb-4">Hệ thống lập kế hoạch và thực thi công cụ thật để xác minh nguyên nhân.</p>
        
        <div className="space-y-4">
          {result.executed_actions.map((act, i) => (
            <div key={i} className="bg-slate-900 border border-slate-700/50 rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/50 flex justify-between items-center">
                <span className="text-sm font-medium text-slate-200">{act.title}</span>
                {act.success ? (
                   <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Success</span>
                ) : (
                   <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">Failed</span>
                )}
              </div>
              <div className="p-4 grid grid-cols-1 gap-3">
                <div className="text-xs">
                  <span className="text-slate-500">Tool: </span><span className="font-mono text-blue-400">{act.tool}</span>
                </div>
                <div className="font-mono text-[11px] text-slate-400 bg-black/40 p-3 rounded overflow-x-auto whitespace-pre-wrap border border-slate-800">
                  {act.output || act.error || "No output returned..."}
                </div>
              </div>
            </div>
          ))}
          {result.executed_actions.length === 0 && <p className="text-sm text-slate-500 italic">Không có công cụ nào được thực thi.</p>}
        </div>
      </div>

      {result.final_diagnosis?.length > 0 && (
         <div className="p-6 bg-emerald-900/10 border border-emerald-500/30 rounded-2xl shadow-xl shadow-emerald-500/5">
           <h3 className="text-lg font-medium text-emerald-400 mb-4 flex items-center gap-2">
             <ShieldAlert className="w-5 h-5"/> Kết luận cuối cùng
           </h3>
           <p className="text-sm font-medium text-slate-200 leading-relaxed mb-6">{result.final_summary}</p>
           <ul className="space-y-3">
             {result.final_diagnosis.map((d, i) => (
               <li key={i} className="flex items-start gap-3 bg-slate-900/40 p-3 rounded-lg border border-emerald-500/10">
                 <CheckCircle2 className="w-4 h-4 mt-0.5 text-emerald-500 shrink-0"/>
                 <span className="text-sm text-slate-300 leading-snug">{d}</span>
               </li>
             ))}
           </ul>
         </div>
      )}
    </div>
  );
}

export function ServiceBreakdownChart({ topServices }: { topServices: Record<string, number> }) {
  if (!topServices || Object.keys(topServices).length === 0) {
    return null;
  }

  const entries = Object.entries(topServices).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(...entries.map(e => e[1]));

  return (
    <div className="p-6 bg-slate-800/40 border border-slate-700/50 rounded-2xl shadow-xl">
      <h3 className="flex items-center gap-2 font-medium text-lg text-slate-200 border-b border-slate-800 pb-3 mb-4">
        <Activity className="w-5 h-5 text-cyan-400"/> Phân bổ lỗi theo dịch vụ
      </h3>
      
      <div className="space-y-5">
        {entries.map(([service, count]) => {
          const percentage = (count / maxCount) * 100;
          const colors = [
            "from-blue-500 to-blue-600",
            "from-indigo-500 to-indigo-600",
            "from-violet-500 to-violet-600",
            "from-cyan-500 to-cyan-600",
            "from-teal-500 to-teal-600",
          ];
          const colorClass = colors[entries.findIndex(e => e[0] === service) % colors.length];

          return (
            <div key={service} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-300 truncate">{service}</span>
                <span className="text-sm font-bold text-slate-200 bg-slate-900/60 px-3 py-1 rounded border border-slate-700">{count}</span>
              </div>
              <div className="w-full bg-slate-900/50 border border-slate-800 rounded-full overflow-hidden h-8">
                <div
                  className={`h-full bg-gradient-to-r ${colorClass} transition-all duration-500 flex items-center justify-end pr-3`}
                  style={{ width: `${percentage}%` }}
                >
                  {percentage > 15 && <span className="text-xs font-bold text-white">{Math.round(percentage)}%</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-700/50">
        <p className="text-xs text-slate-400">
          <span className="font-semibold text-slate-300">Tổng: </span>
          {entries.reduce((sum, [_, count]) => sum + count, 0)} lỗi từ {entries.length} dịch vụ
        </p>
      </div>
    </div>
  );
}
