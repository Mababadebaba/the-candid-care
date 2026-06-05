import { defineConfig } from "sanity";
import { structureTool } from "sanity/structure";
import { visionTool } from "@sanity/vision";

import article from "./schemas/article";
import author from "./schemas/author";
import category from "./schemas/category";

export default defineConfig({
  name: "the-candid-care",
  title: "The Candid Care",
  projectId: import.meta.env.PUBLIC_SANITY_PROJECT_ID || "your-project-id",
  dataset: import.meta.env.PUBLIC_SANITY_DATASET || "production",
  plugins: [structureTool(), visionTool()],
  schema: {
    types: [article, author, category],
  },
});
