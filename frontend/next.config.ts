import type { NextConfig } from "next";

const allowedOrigins = ["127.0.0.1", "localhost"];
if (process.env.TAILSCALE_IP) {
  allowedOrigins.push(process.env.TAILSCALE_IP);
}

const nextConfig: NextConfig = {
  allowedDevOrigins: allowedOrigins,
};

export default nextConfig;
