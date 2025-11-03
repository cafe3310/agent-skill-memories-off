import {z} from 'zod';
import {zodToJsonSchema} from 'zod-to-json-schema';
import {findEntitiesByMetadataQuery, findEntityByNonFrontMatterRegex} from "../retrieval/retrieval.ts";
import {FileType, FrontMatterPresetKeys, type McpHandlerDefinition} from "../../typings.ts";
import {globToRegex} from "../../utils.ts";
import {splitFileIntoSections} from "../editor/editing.ts";
import {normalizeReason} from "../editor/text.ts";

// --- Tool: find_entities_by_metadata ---

export const FindEntitiesByMetadataInput = z.object({
  libraryName: z.string().describe('知识库名称'),
  metadataQuery: z.object({
    [FrontMatterPresetKeys.EntityType]: z.string().optional().describe('实体类型，支持 glob 模式，例如：`Person*`'),
    [FrontMatterPresetKeys.DateModified]: z.string().optional().describe('修改日期，格式为 `YYYY-MM-DD`，支持 glob 模式，例如：`2023-12-*`'),
    [FrontMatterPresetKeys.DateCreated]: z.string().optional().describe('创建日期，格式为 `YYYY-MM-DD`，支持 glob 模式，例如：`*-01-01`'),
    [FrontMatterPresetKeys.RelationAs]: z.string().optional().describe('关系类型，支持 glob 模式，例如：`relation as member:*`'),
    [FrontMatterPresetKeys.Aliases]: z.string().optional().describe('别名，支持 glob 模式，例如：`*alias*`'),
  }).partial().describe('用于在实体元数据中搜索的键值对'),
  reason: z.string().optional().describe('该调用的简要目的'),
});

/**
 * @tool findEntitiesByMetadata
 * @description 根据元数据键值对在实体中进行搜索。
 *
 * @input
 * - `libraryName`: (string, required) 知识库名称。
 * - `metadataQuery`: (object, required) 用于在实体元数据中搜索的键值对。
 * @output
 * - (string) 返回一个 XML 格式的报告，其中包含两部分：
 *   1. `<findEntitiesByMetadata-format-example>`: 展示了输出格式的样例。
 *   2. `<findEntitiesByMetadata RESULT>`: 包含实际的搜索结果。每个匹配的实体都以 `- entityName (matchingKey: matchingValue, ...)` 的格式显示。
 *
 * @remarks
 * - `metadataQuery` 中的值支持 glob 模式匹配。
 * - 输出中的 `matchingValue` 仅列出符合条件的 frontMatter 值，不列出其他的 frontMatter 值。
 */
export const findEntitiesByMetadataTool: McpHandlerDefinition<typeof FindEntitiesByMetadataInput, 'findEntitiesByMetadata'> = {
  toolType: {
    name: 'findEntitiesByMetadata',
    description: '根据元数据键值对在实体中进行搜索。',
    inputSchema: zodToJsonSchema(FindEntitiesByMetadataInput),
  },
  handler: (args: unknown, name) => {
    const { libraryName, metadataQuery, reason } = FindEntitiesByMetadataInput.parse(args);
    const matchingEntities = findEntitiesByMetadataQuery(libraryName, metadataQuery as Record<string, string | boolean>);

    let output = `<${name}-format-example>\n- entityName (matchingKey: matchingValue, matchingKey: matchingValue, ...)\n</${name}-format-example>\n`;
    output += `<${name} reason=${normalizeReason(reason)} RESULT>\n`;

    for (const entityName in matchingEntities) {
      const matchedFrontMatter = matchingEntities[entityName].map(line => {
        const [key, ...valueParts] = line.split(':');
        return `${key.trim()}: ${valueParts.join(':').trim()}`;
      }).join(', ');
      output += `- ${entityName} (${matchedFrontMatter})\n`;
    }
    output += `</${name}>`;

    return output;
  }
};


// --- Tool: find_relations ---

export const FindRelationsInput = z.object({
  libraryName: z.string().describe('The name of the library to search in.'),
  toEntity: z.string().optional().describe('The name of the entity that the relation points to.'),
  relationType: z.string().optional().describe('The type of the relation (e.g., "is-a", "part-of").'),
});



export const SearchAnywhereInput = z.object({
  libraryName: z.string().describe('The name of the library to search in.'),
  pattern: z.string().describe('The glob pattern to search for anywhere.'),
});

// Relation schema for internal use, not directly for tool output schema
z.object({
  from: z.string().describe('The entity where the relation is defined.'),
  to: z.string().describe('The entity the relation points to.'),
  type: z.string().describe('The type of the relation.'),
});

/**
 * @tool find_relations
 * @description 在知识库中查找关系，可选择按目标实体或关系类型进行过滤。
 *
 * @input
 * - `libraryName`: (string, required) 要搜索的知识库的名称。
 * - `toEntity`: (string, optional) 关系指向的目标实体名称。
 * - `relationType`: (string, optional) 关系类型（例如，“is-a”，“part-of”）。
 *
 * @output
 * - (string) 目前返回一个占位符消息，指示该工具尚未完全实现。
 *
 * @remarks
 * - 该工具目前尚未完全实现，调用将返回错误信息。
 * - 预期功能是遍历所有实体，解析其 Front Matter 中的关系，并根据 `toEntity` 和 `relationType` 进行过滤。
 *
 * @todo
 * - [ ] 实现该工具的完整逻辑，包括遍历实体和过滤关系。
 * - [ ] 定义返回的关系数据结构，例如包含 `fromEntity`, `toEntity`, `relationType` 的列表。
 * - [ ] 优化输出格式，使其更符合 XML 规范。
 */
export const findRelationsTool: McpHandlerDefinition<typeof FindRelationsInput, 'find_relations'> = {
  toolType: {
    name: 'find_relations',
    description: 'Finds relations in the knowledge base, optionally filtering by target entity or relation type.',
    inputSchema: zodToJsonSchema(FindRelationsInput),
  },
  handler: (args: unknown) => {
    const {libraryName, toEntity, relationType} = FindRelationsInput.parse(args);
    // Implementation will require iterating through files and parsing front matter.
    // This can be built in the next step.
    // For now, returning a placeholder.
    console.log(libraryName, toEntity, relationType);
    return `---status: success, message: Relations search not fully implemented yet. library: ${libraryName}, toEntity: ${toEntity ?? 'any'}, relationType: ${relationType ?? 'any'}---`;
  }
};

// --- Tool: search_in_contents ---

export const SearchInContentsInput = z.object({
  libraryName: z.string().describe('知识库名称'),
  contentGlob: z.string().describe('用于在实体正文中搜索的 glob 模式'),
  reason: z.string().optional().describe('该调用的简要目的'),
});

/**
 * @tool searchInContents
 * @description 在实体正文中进行 glob 模式匹配，并返回匹配的行及其所在的章节标题。
 *
 * @input
 * - `libraryName`: (string, required) 知识库名称。
 * - `contentGlob`: (string, required) 用于在实体正文中搜索的 glob 模式。
 * - `reason`: (string, optional) 该调用的简要目的。
 *
 * @output
 * - (string) 返回一个 XML 格式的报告，其中包含两部分：
 *   1. `<searchInContents-format-example>`: 展示了输出格式的样例。
 *   2. `<searchInContents RESULT>`: 包含实际的搜索结果。每个匹配的实体都有一个 `===$entityName===` 和 `===$entityName MATCHES END===` 块，其中包含匹配的行及其章节标题。
 *
 * @remarks
 * - Glob 模式匹配是大小写不敏感的。
 * - 如果一个匹配行属于某个章节，其章节标题会以 `##` 的形式显示在匹配行的上方。
 * - 如果实体没有章节，则只显示匹配行。
 */
export const searchInContentsTool: McpHandlerDefinition<typeof SearchInContentsInput, 'searchInContents'> = {
  toolType: {
    name: 'searchInContents',
    description: '在实体正文中进行 glob 模式匹配。',
    inputSchema: zodToJsonSchema(SearchInContentsInput),
  },
  handler: (args: unknown, name) => {
    const { libraryName, contentGlob, reason } = SearchInContentsInput.parse(args);
    const regexPattern = globToRegex(contentGlob);
    const results = findEntityByNonFrontMatterRegex(libraryName, '*.md', regexPattern);

    const resultsByEntity: Record<string, { line: string, toc: string }[]> = {};
    for (const result of results) {
      if (!resultsByEntity[result.name]) {
        resultsByEntity[result.name] = [];
      }
      const sections = splitFileIntoSections(libraryName, FileType.FileTypeEntity, result.name);
      let toc = '';
      for (const section of sections) {
        if (section.content.includes(result.line)) {
          toc = section.tocItem.tocLineContent;
          break;
        }
      }
      resultsByEntity[result.name].push({ line: result.line, toc });
    }

    let output = `<${name}-format-example>\n===$entityName===\n## $tocOfMatchedLines\n$matchedLines\n## $tocOfMatchedLines\n$matchedLines\n===$entityName MATCHES END===\n</${name}-format-example>\n`;
    output += `<${name} reason=${normalizeReason(reason)} RESULT>\n`;

    for (const entityName in resultsByEntity) {
      output += `===${entityName}===\n`;
      for (const match of resultsByEntity[entityName]) {
        if (match.toc) {
          const headingText = match.toc.replace(/^#+\s*/, '');
          output += `## ${headingText}\n`;
        }
        output += `${match.line}\n`;
      }
      output += `===${entityName} MATCHES END===\n`;
    }
    output += `</${name}>`;

    return output;
  }
};



/**
 * @tool search_anywhere
 * @description 在文件名、元数据和正文中进行全局 glob 模式匹配。
 *
 * @input
 * - `libraryName`: (string, required) 要搜索的知识库的名称。
 * - `pattern`: (string, required) 用于在任何地方搜索的 glob 模式。
 *
 * @output
 * - (string) 目前返回一个占位符消息，指示该工具尚未实现。
 *
 * @remarks
 * - 该工具目前尚未实现，调用将返回错误信息。
 *
 * @todo
 * - [ ] 实现该工具的完整逻辑。
 */
export const searchAnywhereTool: McpHandlerDefinition<typeof SearchAnywhereInput, 'search_anywhere'> = {
  toolType: {
    name: 'search_anywhere',
    description: '在文件名、元数据和正文中进行全局 glob 模式匹配。',
    inputSchema: zodToJsonSchema(SearchAnywhereInput),
  },
  handler: (args: unknown) => {
    return `---status: failed, message: search_anywhere tool is not yet implemented.---`;
  }
};

// Export all tools as an array, similar to entity.ts
export const retrievalTools = [findEntitiesByMetadataTool, findRelationsTool, searchInContentsTool, searchAnywhereTool];
