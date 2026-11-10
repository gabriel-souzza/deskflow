import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: [
    // Rede local física (Wi-Fi / Ethernet - Celular)
    "192.168.1.3",
    "192.168.1.3:3000",
    // Interfaces virtuais e containers (WSL / Hyper-V)
    "172.26.32.1",
    "172.26.32.1:3000",
    "192.168.96.1",
    "192.168.96.1:3000",
    // Localhost
    "localhost",
    "localhost:3000",
    "127.0.0.1",
    "127.0.0.1:3000",
  ],
};

export default nextConfig;

