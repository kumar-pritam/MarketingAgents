import { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || "https://marketingagents.ai";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/agents",
    "/workspaces",
    "/history",
  ];

  return routes.map((route) => ({
    url: `${BASE_URL}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : route === "/agents" ? 0.9 : 0.7,
  }));
}
