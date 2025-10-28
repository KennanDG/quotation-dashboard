import { z } from "zod";

export const ProjectSchema = z.object({
  id: z.string().uuid().optional(),
  name: z.string(),
  serviceType: z.enum(["design", "pcba", "im", "prototyping"]),
  status: z.enum(["draft", "in_progress", "approved"]).default("draft"),
});
export type Project = z.infer<typeof ProjectSchema>;