import {z} from 'zod';
import {zodToJsonSchema} from 'zod-to-json-schema';
import {getLibraryNames} from "@src/runtime.ts";
import {normalizeReason} from "@src/basics/text.ts";
import type {McpHandlerDefinition} from "@src/features/types.ts";
import {readFileContent} from "@src/basics/file-ops.ts";
import {FileType} from "@src/entities/editor/types.ts";

const LoadManualInputSchema = z.object({
  libraryName: z.string().describe('目标知识库的名称, 可用值: ' + getLibraryNames()),
  reason: z.string().optional().describe('调用此工具的简要原因'),
});

/**
 * @tool loadManual
 *
 * @description
 * - 读取知识库的 `meta.md` 文件，获取全局描述、规则和指导原则。
 *
 * @input
 * - libraryName: (string, required) 目标知识库的名称。
 * - reason: (string, optional) 调用此工具的简要原因。
 *
 * @output
 * - XML 报告，内含完整的 Markdown 文本。
 *   一个实际的例子如下：
 *
 *   ```xml
 *   <loadManual reason=了解知识库的规则和指导原则 CONTENT>
 *     # 知识库元信息
 *     本知识库包含以下规则和指导原则：
 *     # 格式要求
 *     - 所有条目必须遵循统一的格式。
 *   </loadManual>
 *   ```
 *
 * @see docs/2026-01-04-22-25-tools-spec.md - loadManual
 */
export const loadManualTool: McpHandlerDefinition<typeof LoadManualInputSchema, 'loadManual'> = {
  toolType: {
    name: 'loadManual',
    description: '读取知识库的 `meta.md` 文件，获取全局描述、规则和指导原则。',
    inputSchema: zodToJsonSchema(LoadManualInputSchema),
  },
  handler: (args, name) => {
    const {libraryName, reason} = LoadManualInputSchema.parse(args);
    const lines = readFileContent({library: libraryName, type: FileType.FileTypeMeta, name: ''});

    return `<${name} reason=${normalizeReason(reason)} CONTENT>
${lines.join('\n')}
</${name}>`;
  },
};
