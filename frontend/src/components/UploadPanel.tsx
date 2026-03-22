import { UploadCloud, FileText, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";

interface UploadPanelProps {
  file: File | null;
  setFile: (f: File | null) => void;
  query: string;
  setQuery: (q: string) => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
}

export function UploadPanel({ file, setFile, query, setQuery, onAnalyze, isAnalyzing }: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        setFile(e.dataTransfer.files[0]);
      }
    },
    [setFile]
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-slate-800/40 rounded-2xl border border-slate-700/50 shadow-xl">
      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all ${
          isDragging ? "border-blue-400 bg-blue-500/10" : "border-slate-600 hover:border-slate-500 hover:bg-slate-800/60"
        } ${file ? "border-emerald-500/50 bg-emerald-500/5" : ""}`}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
          }}
        />
        
        {file ? (
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="p-3 bg-emerald-500/20 rounded-full">
              <FileText className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <p className="font-medium text-slate-200">{file.name}</p>
              <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-red-400 bg-slate-800 rounded-md transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 text-center cursor-pointer" onClick={() => fileInputRef.current?.click()}>
            <div className="p-4 bg-slate-800 rounded-full shadow-inner border border-slate-700">
              <UploadCloud className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <p className="font-medium text-slate-300">Kéo thả file log Apache vào đây</p>
              <p className="text-sm text-slate-500 mt-1">hoặc nhấn để chọn file</p>
            </div>
          </div>
        )}
      </div>

      {/* Query Zone */}
      <div className="flex flex-col gap-4">
        <div className="flex-1 flex flex-col">
          <label className="text-sm font-medium text-slate-300 mb-2 flex justify-between items-center">
            <span>Yêu cầu điều tra (Tùy chọn)</span>
            <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">RAG Focus</span>
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isAnalyzing}
            placeholder="Ví dụ: Chỉ phân tích các dấu hiệu cho thấy Tomcat chết hoặc AJP port không mở, bỏ qua lỗi truy cập thư mục..."
            className="flex-1 w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none transition-all disabled:opacity-50"
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={onAnalyze}
            disabled={!file || isAnalyzing}
            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 disabled:shadow-none"
          >
            {isAnalyzing ? "Đang xử lý..." : "Phân tích Log"}
          </button>
        </div>
        {!file && (
          <p className="text-xs text-center text-slate-500">
            Hệ thống sẽ Parse Log ➔ AI phân cụm ➔ Truy xuất KB (RAG) ➔ Chạy Tools ➔ Kết luận
          </p>
        )}
      </div>
    </div>
  );
}
