import type {
  Document,
  ThingLocator
} from "@src/entities/editor/types.ts";
import {fileExists, readFileContent} from "@src/basics/file-ops.ts";
import {locateFrontMatter, readFrontMatter} from "@src/entities/editor/front-matter.ts";
import {checks, deepFreeze} from "@src/basics/utils.ts";
import {getToc} from "@src/entities/editor/toc.ts";

// 将一个文件解析成 Document 结构
// 包含 toc, frontmatter 和各个 section 信息
export function parseDocument(target: ThingLocator) {

  // 文件存在
  const isExist = fileExists(target);
  checks(isExist, `目标文件不存在`);

  // 读取内容
  const fileContent = readFileContent(target);

  // 读 front-matter
  const frontMatterLocator = locateFrontMatter(target);
  const frontMatter = readFrontMatter(target);

  // 读 toc
  const toc = getToc(target);

  // 从 frontmatter 最后一行开始确定正文起始位置；
  // 然后一段段截取每个 toc 对应的正文内容，构建 Document.sections。
  // 考虑 toc 之前可能有正文内容的情况。
  const sections: Document["sections"] = [];

  // 正文起始行
  let bodyStartLineNumber = 1;
  if (frontMatterLocator) {
    bodyStartLineNumber = frontMatterLocator.endLineNumber + 1;
  }

  // 第一个 toc 之前的正文内容
  if (toc.length > 0) {
    const firstToc = toc[0]!;
    if (firstToc.lineNumber > bodyStartLineNumber) {
      const sectionStartLineNumber = bodyStartLineNumber;
      const sectionEndLineNumber = firstToc.lineNumber - 1;
      const content = fileContent.slice(sectionStartLineNumber - 1, sectionEndLineNumber);
      sections.push({
        locator: {
          target: target,
          origin: 'document',
          beginLineNumber: sectionStartLineNumber,
          endLineNumber: sectionEndLineNumber,
          beginContentLine: fileContent[sectionStartLineNumber - 1]!,
          endContentLine: fileContent[sectionEndLineNumber - 1]!,
        },
        content: content,
      });
    }
  }

  // 然后，处理每个 toc 之后的正文内容。注意，toc 之间的正文可能是空的。
  for (let i = 0; i < toc.length; i++) {
    const currentToc = toc[i]!;
    const nextToc = toc[i + 1];

    const sectionLineStart = currentToc.lineNumber + 1;
    const sectionLineEnd = nextToc ? nextToc.lineNumber - 1 : fileContent.length;
    const content = fileContent.slice(sectionLineStart - 1, sectionLineEnd);

    sections.push({
      heading: currentToc,
      locator: {
        target: target,
        origin: 'document',
        beginLineNumber: sectionLineStart,
        endLineNumber: sectionLineEnd,
        beginContentLine: fileContent[sectionLineStart - 1]!,
        endContentLine: fileContent[sectionLineEnd - 1]!,
      },
      content: content,
    });
  }

  return deepFreeze({
    locator: target,
    frontmatter: frontMatter,
    toc: toc,
    sections: sections,
    fileContent: fileContent,
  });
}
