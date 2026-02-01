import type { NextConfig } from "next";

const frontendDevPort = 3000;
const backendDevPort = 8000;

const nextConfig: NextConfig = {
  /* config options here */
  output: "export",
  reactCompiler: true,
  turbopack: {
    root: __dirname,
  },
  env: {
    PORT: frontendDevPort.toString(),
    NEXT_PUBLIC_API_URL: 'http://localhost:' + backendDevPort,
  },
};

export default nextConfig;
