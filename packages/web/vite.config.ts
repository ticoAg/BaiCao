import { defineConfig } from "vite-plus";
import react from "@vitejs/plugin-react";

const apiProxyTarget = process.env.WEB_API_BASE_URL ?? "http://localhost:8000";

function resolveGraphChunk(id: string) {
  if (!id.includes("/node_modules/")) {
    return undefined;
  }

  const graphAlgorithmPackages = [
    "dagre",
    "d3-force",
    "d3-quadtree",
    "d3-timer",
    "d3-dispatch",
  ];

  if (graphAlgorithmPackages.some((pkg) => id.includes(pkg))) {
    return "graph-layout";
  }

  const match = id.match(/\/node_modules\/\.pnpm\/((?:@[^/+]+\+)?[^@/]+)@/);
  if (match?.[1]) {
    const encodedPackage = match[1];
    const isGraphPackage =
      encodedPackage.startsWith("@antv+") ||
      encodedPackage.startsWith("@ant-design+graphs");

    if (isGraphPackage) {
      return `graph-${encodedPackage.replaceAll("@", "").replaceAll("+", "-")}`;
    }
  }

  return undefined;
}

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1200,
    rolldownOptions: {
      output: {
        manualChunks(id) {
          return resolveGraphChunk(id);
        },
      },
    },
  },
  resolve: {
    alias: {
      "@": "/src",
      "@bai-cao/shared": "/shared/types",
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      reportsDirectory: "./coverage",
    },
  },
});
