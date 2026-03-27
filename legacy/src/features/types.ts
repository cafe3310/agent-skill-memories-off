// region 工具 typings

import {z, type ZodTypeAny} from "zod";

export type McpHandlerDefinition<Args extends ZodTypeAny, Name extends string> = {
  toolType: {
    name: Name;
    description: string;
    inputSchema: unknown;
  };
  handler: (args: z.infer<Args>, toolName: Name, extra?: unknown) => string;
}

// endregion
