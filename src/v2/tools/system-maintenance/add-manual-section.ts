import {z} from 'zod';
import {zodToJsonSchema} from 'zod-to-json-schema';
import {getLibraryNames} from "@src/runtime.ts";
import {normalizeReason, textToHeading} from "@src/basics/text.ts";
import type {McpHandlerDefinition} from "@src/features/types.ts";
import {FileType} from "@src/entities/editor/types.ts";
import {addContentToThing} from "@src/entities/editor/editing.ts";

const AddManualSectionInputSchema = z.object({
  libraryName: z.string().describe('目标知识库的名称, 可用值: ' + getLibraryNames()),
  sectionTitle: z.string().describe('新章节的标题'),
  newContent: z.string().describe('新章节的内容'),
  reason: z.string().optional().describe('修改原因'),
});

/**
 * @tool addManualSection
 * @description 在 `meta.md` 文件末尾追加新的章节。
 * 
 * @input
 * - `libraryName`: (string, required) 目标知识库的名称。
 * - `sectionTitle`: (string, required) 新章节的标题。
 * - `newContent`: (string, required) 新章节的内容。
 * - `reason`: (string, optional) 修改原因。
 * 
 * @output
 * - XML 报告，指示操作成功。
 * 
 * @see docs/2026-01-04-22-25-tools-spec.md
 */
export const addManualSectionTool: McpHandlerDefinition<typeof AddManualSectionInputSchema, 'addManualSection'> = {
  toolType: {
    name: 'addManualSection',
    description: '在 `meta.md` 文件末尾追加新的章节。',
    inputSchema: zodToJsonSchema(AddManualSectionInputSchema),
  },
  handler: (args, name) => {
    const {libraryName, sectionTitle, newContent, reason} = AddManualSectionInputSchema.parse(args);

    const target = {
      library: libraryName,
      type: FileType.FileTypeMeta,
      name: '',
    };

    // 格式化标题行 (默认二级标题)
    const titleLine = textToHeading(sectionTitle, 2);
    // 准备要追加的内容行
    const contentLines = newContent.split('\n');
    
    // 组合标题和内容
    const linesToAdd = ['', titleLine, ...contentLines];

    addContentToThing(target, linesToAdd);

    return `<${name} reason="${normalizeReason(reason)}">
success
</${name}>`;
  },
};
