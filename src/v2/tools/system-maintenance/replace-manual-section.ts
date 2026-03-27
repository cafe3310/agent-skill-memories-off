import {z} from 'zod';
import {zodToJsonSchema} from 'zod-to-json-schema';
import {getLibraryNames} from "@src/runtime.ts";
import {normalizeReason} from "@src/basics/text.ts";
import type {McpHandlerDefinition} from "@src/features/types.ts";
import {readFileContent} from "@src/basics/file-ops.ts";
import {FileType, type ThingLocator} from "@src/entities/editor/types.ts";
import {replaceSection} from "@src/entities/editor/editing.ts";

const ReplaceManualSectionInputSchema = z.object({
  libraryName: z.string().describe('目标知识库的名称, 可用值: ' + getLibraryNames()),
  sectionTitle: z.string().describe('目标章节的 SectionHeading (不含#), 必须精确匹配'),
  newContent: z.string().describe('新的 Markdown 内容'),
  reason: z.string().optional().describe('修改原因'),
});

/**
 * @tool replaceManualSection
 *
 * @description
 * - 更新 `meta.md` 文件中的特定章节，用于修改全局规则或描述。必须提供精确的章节标题。
 *
 * @input
 * - `libraryName`: (string, required) 目标知识库的名称。
 * - `sectionTitle`: (string, required) 目标章节的标题（不包含 # 符号）。
 * - `newContent`: (string, required) 用来替换旧章节的新 Markdown 内容。
 * - `reason`: (string, optional) 修改原因。
 *
 * @output
 * - XML 报告，包含更新后的 `meta.md` 片段。
 *
 *   示例:
 *
 *   ```xml
 *   <replaceManualSection reason="更新使用条款">
 *     # 知识库使用条款
 *     这里是更新后的使用条款内容...
 *     # 其他章节
 *     这里是其他章节内容...
 *   </replaceManualSection>
 *
 * @see docs/2026-01-04-22-25-tools-spec.md - replaceManualSection
 */
export const replaceManualSectionTool: McpHandlerDefinition<typeof ReplaceManualSectionInputSchema, 'replaceManualSection'> = {
  toolType: {
    name: 'replaceManualSection',
    description: '更新 `meta.md` 文件中的特定章节。',
    inputSchema: zodToJsonSchema(ReplaceManualSectionInputSchema),
  },
  handler: (args, name) => {
    const {libraryName, sectionTitle, newContent, reason} = ReplaceManualSectionInputSchema.parse(args);

    const target: ThingLocator = {
      library: libraryName,
      type: FileType.FileTypeMeta,
      name: '',
    };

    // 执行替换
    // newContent 需要按行分割
    const contentLines = newContent.split('\n');
    replaceSection(target, sectionTitle, contentLines);

    // 输出更新后的全文
    const updatedMetaContent = readFileContent(target);

    return `<${name} reason=${normalizeReason(reason)} CONTENT>
${updatedMetaContent.join('\n')}
</${name}>`;
  },
};
