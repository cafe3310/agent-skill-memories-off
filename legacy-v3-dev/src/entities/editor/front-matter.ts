import {readFileContent, writeFileContent} from "@src/basics/file-ops.ts";
import {
  type FrontMatter,
  FrontMatterPresetKeys, type ResolvedContentLocator,
  type ThingLocator,
} from "@src/entities/editor/types.ts";


// 定位指定实体的 Front Matter 位置
// 返回 null 表示不存在 Front Matter，否则返回对应的 ResolvedContentLocator
export function locateFrontMatter(target: ThingLocator): ResolvedContentLocator | null {
  const content = readFileContent(target);
  if (content[0]?.trim() !== '---') {
    return null;
  }
  const endLineIndex = content.slice(1).findIndex(line => line.trim() === '---');
  if (endLineIndex === -1) {
    return null;
  }
  return {
    target: target,
    origin: 'frontmatter',
    beginLineNumber: 1,
    endLineNumber: endLineIndex + 2,
    beginContentLine: content[0],
    endContentLine: content[endLineIndex + 1]!,
  };
}

// 合并两个 Front Matter 信息
// 对特殊的 key 进行合并去重处理
// 其余 key 则直接拼接
export function mergeFrontMatter(target: FrontMatter, source: FrontMatter): FrontMatter {
  const merged = new Map<string, string>();

  // 先将 target 全添加了
  for (const item of target) {
    merged.set(item.name, item.value);
  }

  // 然后合并 source
  for (const item of source) {

    if (merged.has(item.name)) {

      const existingValue = merged.get(item.name) ?? '';

      if ((item.name === FrontMatterPresetKeys.Aliases as string)
        || (item.name === FrontMatterPresetKeys.EntityType as string)) {
        // 'alias' 和 'type' -- 按 `,` 分割，合并去重
        const targetAliases = existingValue.split(',').map(s => s.trim());
        const sourceAliases = item.value.split(',').map(s => s.trim());
        const combined = [...new Set([...targetAliases, ...sourceAliases])];
        merged.set(item.name, combined.join(', '));
      } else {
        // 其他 key -- 直接拼接
        // 包括 relation as x: y; date created; date modified 等等
        if (existingValue !== item.value) {
          merged.set(item.name, `${existingValue}, ${item.value}`);
        }
      }
    } else {
      // source 中的新 key 直接添加
      merged.set(item.name, item.value);
    }
  }

  // build a FrontMatter array from the map
  const result: FrontMatter = [];
  for (const [name, value] of merged.entries()) {
    result.push({ name, value });
  }
  return result;
}

// 读取指定实体的 Front Matter 信息
export function readFrontMatter(target: ThingLocator): FrontMatter {

  const content = readFileContent(target);

  const frontMatterEndIndex = content.findIndex((line, index) => index > 0 && line.trim() === '---');
  if (frontMatterEndIndex === -1 || !content[0]?.startsWith('---')) {
    return [] as FrontMatter;
  }

  const lines = content.slice(1, frontMatterEndIndex);
  if (!lines) {
    return [] as FrontMatter;
  }

  const frontMatter: FrontMatter = [];
  for (const line of lines) {
    // 按 yaml 语法简单解析 name-value 对。处理以下情况：
    // name: value (name 和 value 之间有一个或多个空格)
    // name:       (name 后面有多个空格，但没有 value)
    // name        (只有 name，没有冒号和 value)
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) {
      // 没有冒号，整个行作为 name，value 为空
      frontMatter.push({ name: line.trim(), value: '' });
    } else {
      const name = line.slice(0, colonIndex).trim();
      const value = line.slice(colonIndex + 1).trim();
      frontMatter.push({ name, value });
    }
  }
  return frontMatter;
}

// 写入指定实体的 Front Matter 信息
export function writeFrontMatter(target: ThingLocator, frontMatter: FrontMatter): void {

  const lines = readFileContent(target);

  const frontMatterEndIndex = lines.findIndex((line, index) => index > 0 && line.trim() === '---');

  const hasFrontMatter = frontMatterEndIndex !== -1 && lines[0]?.startsWith('---');

  let contentLines: string[];
  if (hasFrontMatter) {
    contentLines = lines.slice(frontMatterEndIndex + 1);
  } else {
    contentLines = lines;
  }

  const frontMatterLines = frontMatter.map(item => `${item.name}: ${item.value}`);
  const newLines = [
    '---',
    ...(frontMatterLines),
    '---',
    ...contentLines,
  ];

  writeFileContent(target, newLines);
}
