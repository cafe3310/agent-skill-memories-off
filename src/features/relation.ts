import {z} from 'zod';
import {zodToJsonSchema} from 'zod-to-json-schema';
import {normalizeReason} from "@src/basics/text.ts";
import type {McpHandlerDefinition} from "@src/features/types.ts";
import {readFrontMatter, writeFrontMatter} from "@src/entities/editor/front-matter.ts";
import {FileType, type FrontMatterLine, FrontMatterPresetKeys} from "@src/entities/editor/types.ts";

const RelationSchema = z.object({
  type: z.string().describe('关系类型'),
  to: z.string().describe('关系指向的实体名称'),
});

export const CreateRelationsInputSchema = z.object({
  libraryName: z.string().describe('知识库名称'),
  relations: z.union([z.string(), z.array(z.string())]).describe('要创建的关系，格式为 “source, verb, target” 的字符串或字符串数组'),
  reason: z.string().optional().describe('该调用的简要目的'),
});

/**
 * @tool createRelations
 * @description 在一个或多个实体的 Front Matter 中批量添加关系。关系以 `relation <verb>: <target>` 的形式存储。
 *
 * @input
 * - `libraryName`: (string, required) 知识库的名称。
 * - `relations`: (string | string[], required) 要创建的关系，格式为 “source, verb, target” 的字符串或字符串数组。
 * - `reason`: (string, optional) 本次操作的简要目的说明。
 *
 * @output
 * - (string) 返回一个 XML 格式的报告，其中包含两个部分：
 *   1. `<createRelations CREATED RELATIONS>`: 列出所有成功创建的关系。
 *   2. `<createRelations FAILED RELATIONS>`: 列出所有创建失败的关系及其原因。
 *
 * @remarks
 * - 关系存储在 `source` 实体的 Front Matter 中。
 * - 如果关系已存在，工具会忽略，不会重复添加。
 * - 如果 `source` 实体不存在，创建会失败。
 * - 不会验证 `target` 实体是否存在。
 */
export const createRelationsTool: McpHandlerDefinition<typeof CreateRelationsInputSchema, 'createRelations'> = {
  toolType: {
    name: 'createRelations',
    description: '在一个或多个实体的 Front Matter 中批量添加关系',
    inputSchema: zodToJsonSchema(CreateRelationsInputSchema),
  },
  handler: (args: unknown, name) => {
    const { libraryName, relations, reason } = CreateRelationsInputSchema.parse(args);
    const relationsArr = Array.isArray(relations) ? relations : [relations];

    const parsedRelations = relationsArr.map(r => {
      const parts = r.split(',').map(p => p.trim());
      return { source: parts[0], verb: parts[1], target: parts[2] };
    });

    const createdRelations: { source: string, verb: string, target: string }[] = [];
    const failedRelations: { source: string, verb: string, target: string, reason: string }[] = [];

    const relationsBySource = parsedRelations.reduce((acc, rel) => {
      if (!rel.source || !rel.verb || !rel.target) return acc;
      if (!acc[rel.source]) {
        acc[rel.source] = [];
      }
      acc[rel.source].push(rel);
      return acc;
    }, {} as Record<string, typeof parsedRelations>);

    for (const sourceEntity in relationsBySource) {
      try {
        const existingFrontMatter = readFrontMatter({library: libraryName, fileType: FileType.FileTypeEntity, entityName: sourceEntity});
        const newFrontMatter = [...existingFrontMatter];
        const relationsForSource = relationsBySource[sourceEntity];

        for (const relation of relationsForSource) {
          const relationLine = `${FrontMatterPresetKeys.RelationAs} ${relation.verb}: ${relation.target}` as FrontMatterLine;
          if (!newFrontMatter.includes(relationLine)) {
            newFrontMatter.push(relationLine);
            createdRelations.push(relation);
          }
        }

        if (newFrontMatter.length > existingFrontMatter.length) {
          writeFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: sourceEntity}, newFrontMatter);
        }
      } catch (error) {
        relationsBySource[sourceEntity].forEach(rel => {
          failedRelations.push({ ...rel, reason: (error as Error).message });
        });
      }
    }

    let result = '';
    if (createdRelations.length > 0) {
      result += `<${name} reason=${normalizeReason(reason)} CREATED RELATIONS>\n`;
      result += createdRelations.map(r => `- ${r.source}, ${r.verb}, ${r.target}`).join('\n');
      result += `\n</${name}>`;
    }

    if (failedRelations.length > 0) {
      if (result) result += '\n';
      result += `<${name} reason=${normalizeReason(reason)} FAILED RELATIONS>\n`;
      result += failedRelations.map(r => `- ${r.source}, ${r.verb}, ${r.target}: ${r.reason}`).join('\n');
      result += `\n</${name}>`;
    }

    return result || `<${name} reason=${normalizeReason(reason)} NO ACTION TAKEN>\nNo new relations were created.\n</${name}>`;
  },
};


export const DeleteRelationsInputSchema = z.object({
  libraryName: z.string().describe('知识库名称'),
  relations: z.union([z.string(), z.array(z.string())]).describe('要删除的关系，格式为 “source, verb, target” 的字符串或字符串数组'),
  reason: z.string().optional().describe('该调用的简要目的'),
});

/**
 * @tool deleteRelations
 * @description 从一个或多个实体的 Front Matter 中批量删除关系。
 *
 * @input
 * - `libraryName`: (string, required) 知识库的名称。
 * - `relations`: (string | string[], required) 要删除的关系，格式为 “source, verb, target” 的字符串或字符串数组。
 * - `reason`: (string, optional) 本次操作的简要目的说明。
 *
 * @output
 * - (string) 返回一个 XML 格式的报告，其中包含两个部分：
 *   1. `<deleteRelations DELETED RELATIONS>`: 列出所有成功删除的关系。
 *   2. `<deleteRelations FAILED RELATIONS>`: 列出所有删除失败的关系及其原因。
 *
 * @remarks
 * - 只有当 `source`, `verb`, 和 `target` 都精确匹配时，关系才会被删除。
 */
export const deleteRelationsTool: McpHandlerDefinition<typeof DeleteRelationsInputSchema, 'deleteRelations'> = {
  toolType: {
    name: 'deleteRelations',
    description: '从一个或多个实体的 Front Matter 中批量删除关系',
    inputSchema: zodToJsonSchema(DeleteRelationsInputSchema),
  },
  handler: (args: unknown, name) => {
    const { libraryName, relations, reason } = DeleteRelationsInputSchema.parse(args);
    const relationsArr = Array.isArray(relations) ? relations : [relations];

    const parsedRelations = relationsArr.map(r => {
      const parts = r.split(',').map(p => p.trim());
      return { source: parts[0], verb: parts[1], target: parts[2] };
    });

    const deletedRelations: { source: string, verb: string, target: string }[] = [];
    const failedRelations: { source: string, verb: string, target: string, reason: string }[] = [];

    const relationsBySource = parsedRelations.reduce((acc, rel) => {
      if (!rel.source || !rel.verb || !rel.target) return acc;
      if (!acc[rel.source]) {
        acc[rel.source] = [];
      }
      acc[rel.source].push(rel);
      return acc;
    }, {} as Record<string, typeof parsedRelations>);

    for (const sourceEntity in relationsBySource) {
      try {
        const existingFrontMatter = readFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: sourceEntity});
        const relationsToDeleteForSource = relationsBySource[sourceEntity];
        let linesChanged = false;

        const newFrontMatter = existingFrontMatter.filter(line => {
          const isRelationLine = line.startsWith(`${FrontMatterPresetKeys.RelationAs} `);
          if (!isRelationLine) {
            return true; // Keep non-relation lines
          }

          const [prefix, rest] = line.split(': ', 2);
          const verb = (prefix ?? '').replace(`${FrontMatterPresetKeys.RelationAs} `, '');
          const target = rest;

          const shouldDelete = relationsToDeleteForSource.some(r => r.verb === verb && r.target === target);
          if (shouldDelete) {
            const deletedRel = relationsToDeleteForSource.find(r => r.verb === verb && r.target === target);
            if(deletedRel) deletedRelations.push(deletedRel);
            linesChanged = true;
            return false; // Delete this line
          }
          return true; // Keep this relation line
        });

        if (linesChanged) {
          writeFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: sourceEntity}, newFrontMatter);
        }
      } catch (error) {
        relationsBySource[sourceEntity].forEach(rel => {
          failedRelations.push({ ...rel, reason: (error as Error).message });
        });
      }
    }

    let result = '';
    if (deletedRelations.length > 0) {
      result += `<${name} reason=${normalizeReason(reason)} DELETED RELATIONS>\n`;
      result += deletedRelations.map(r => `- ${r.source}, ${r.verb}, ${r.target}`).join('\n');
      result += `\n</${name}>`;
    }

    if (failedRelations.length > 0) {
      if (result) result += '\n';
      result += `<${name} reason=${normalizeReason(reason)} FAILED RELATIONS>\n`;
      result += failedRelations.map(r => `- ${r.source}, ${r.verb}, ${r.target}: ${r.reason}`).join('\n');
      result += `\n</${name}>`;
    }

    return result || `<${name} reason=${normalizeReason(reason)} NO ACTION TAKEN>\nNo relations were deleted.\n</${name}>`;
  },
};

export const relationTools = [createRelationsTool, deleteRelationsTool];
