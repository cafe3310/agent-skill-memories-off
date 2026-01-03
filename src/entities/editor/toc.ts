import {pathForFile, readFileContent} from "@src/basics/file-ops.ts";
import {
  type HeadingGlob,
  type Heading,
  type Toc, type ThingLocator
} from "@src/entities/editor/types.ts";
import {normalizeHeading} from "@src/basics/text.ts";
import {checks} from "@src/basics/utils.ts";

// 获取库中 Thing 的完整 ToC 结构。
export function getToc(target: ThingLocator): Toc {
  const toc: Toc = [];
  readFileContent(target.library, target.type, target.name)
    .forEach((line, index) => {
      if (line.startsWith('#')) {
        const level = (/^#+/.exec(line))?.[0].length ?? 1;
        toc.push({
          level: level,
          lineNumber: (index + 1),
          text: line,
        });
      }
    });
  return toc;
}

// 尝试在目标文件的所有章节标题中查找匹配的，返回所有匹配项（可能为空）
export function matchHeadingInTocNoThrow(target: ThingLocator, headingGlob: HeadingGlob): Heading[] {
  const tocList = getToc(target);
  const normalizedGlob = normalizeHeading(headingGlob);
  return tocList.filter(item => normalizeHeading(item.text) === normalizedGlob);
}

// 在目标文件的章节标题中查找唯一匹配的标题，未找到或多于一个均抛出错误
export function matchHeadingInToc(target: ThingLocator, glob: HeadingGlob): Heading {
  const matches = matchHeadingInTocNoThrow(target, glob);
  checks(matches.length !== 0, `在文件 ${pathForFile(target.library, target.type, target.name)} 中未找到与 '${glob}' 匹配的章节标题。`);
  checks(matches.length === 1, `发现多个与 '${glob}' 匹配的章节标题，请提供更精确的标题：\n- ${matches.map(m => m.text).join('\n- ')}`);
  return matches[0]!;
}
