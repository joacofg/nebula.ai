import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // The dev badge overlaps the rail footer and would end up in the thesis screenshots.
  devIndicators: false,
};

export default nextConfig;
