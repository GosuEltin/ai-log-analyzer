import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "vietnamese"] });

export const metadata: Metadata = {
  title: "AI Log Analyzer",
  description: "Phân tích, điều tra và hiển thị log hệ thống",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark">
      <body className={`${inter.className} min-h-screen antialiased bg-slate-900 text-slate-50`}>
        {children}
      </body>
    </html>
  );
}
