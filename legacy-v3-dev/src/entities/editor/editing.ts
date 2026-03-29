import {
  type ContentLineExact,
  type ContentLineNumber,
  type ContentLocator,
  type FileContent,
  type HeadingGlob,
  type ThingLocator
} from "@src/entities/editor/types.ts";
import {readFileContent, writeFileContent} from "@src/basics/file-ops.ts";
import {matchHeadingInToc} from "./toc.ts";
import {resolveContentLocator} from "./locator.ts";
import {parseDocument} from "@src/entities/editor/document.ts";
import {checks} from "@src/basics/utils.ts";

// 在文件中替换内容
// 仅当可定位到唯一内容时，才进行替换操作
// 如果 newContent 为空数组，则表示删除定位到的内容
export function replaceContent(target: ThingLocator, oldContent: ContentLocator, newContent: ContentLineExact[]): void {
  const content = readFileContent(target);
  const resolved = resolveContentLocator(target, oldContent);
  if (!resolved) {
    throw new Error(`替换内容不唯一或无法定位到，替换失败`);
  }
  const updateContent: FileContent = innerReplace(content, resolved.beginLineNumber, resolved.endLineNumber, newContent);
  writeFileContent(target, updateContent);
}

// 在文件指定的章节中替换内容
// 仅当可定位到唯一章节和唯一内容时，才进行替换操作
// 如果 newContent 为空数组，则表示删除定位到的内容
export function replaceInHeading(target: ThingLocator, headingLocator: HeadingGlob, oldContent: ContentLocator, newContent: ContentLineExact[]): void {

  const doc = parseDocument(target);

  // 唯一匹配章节
  const matchedToc = matchHeadingInToc(target, headingLocator);
  const tocLineNumber = matchedToc.lineNumber;

  // 在 doc 中找到这个章节
  const found = doc.sections.find(section => section.heading?.lineNumber === tocLineNumber);

  checks(!!found, `在 ${target.library} 库的 ${target.type} 类型的 ${target.name} 中，未找到章节 ${JSON.stringify(headingLocator)}`);

  // 在章节范围内，定位内容
  const resolved = resolveContentLocator(target, oldContent, {
    searchStartLine: found.locator.beginLineNumber,
    searchEndLine: found.locator.endLineNumber
  });

  checks(!!resolved, `在 ${target.library} 库的 ${target.type} 类型的 ${target.name} 中，章节 ${JSON.stringify(headingLocator)} 内未找到内容 ${JSON.stringify(oldContent)}`);

  // 替换内容并保存
  const newFileContent = innerReplace(doc.fileContent, resolved.beginLineNumber, resolved.endLineNumber, newContent);
  writeFileContent(target, newFileContent);
}

// 完整替换指定章节的内容
// 仅当可定位到唯一章节时，才进行替换操作
export function replaceSection(target: ThingLocator, headingLocator: HeadingGlob, newContent: ContentLineExact[]): void {
  const doc = parseDocument(target);

  // 唯一匹配章节
  const matchedToc = matchHeadingInToc(target, headingLocator);
  const tocLineNumber = matchedToc.lineNumber;

  // 在 doc 中找到这个章节
  const found = doc.sections.find(section => section.heading?.lineNumber === tocLineNumber);

  checks(!!found, `在 ${target.library} 库的 ${target.type} 类型的 ${target.name} 中，未找到章节 ${JSON.stringify(headingLocator)}`);

  // 替换内容并保存
  const newFileContent = innerReplace(doc.fileContent, found.locator.beginLineNumber, found.locator.endLineNumber, newContent);
  writeFileContent(target, newFileContent);
}

// 在文件末尾添加内容
export function addContentToThing(target: ThingLocator, content: ContentLineExact[]): void {
  const oldContent = readFileContent(target);
  const newContent = innerReplace(oldContent, oldContent.length + 1, oldContent.length, content);
  writeFileContent(target, newContent);
}

// 在指定的章节末尾添加内容
// 仅当可定位到唯一章节时，才进行添加操作
// 如果 newContent 为空数组，则不进行任何操作
export function appendInHeading(target: ThingLocator, headingLocator: HeadingGlob, newContent: ContentLineExact[]): void {
  const doc = parseDocument(target);

  // 唯一匹配章节
  const matchedToc = matchHeadingInToc(target, headingLocator);
  const tocLineNumber = matchedToc.lineNumber;

  // 在 doc 中找到这个章节
  const found = doc.sections.find(section => section.heading?.lineNumber === tocLineNumber);

  checks(!!found, `在 ${target.library} 库的 ${target.type} 类型的 ${target.name} 中，未找到章节 ${JSON.stringify(headingLocator)}`);

  // 在章节范围内，定位内容
  const insertLineNumber = found.locator.endLineNumber + 1;

  // 插入内容并保存
  const newFileContent = innerReplace(doc.fileContent, insertLineNumber, insertLineNumber - 1, newContent);
  writeFileContent(target, newFileContent);
}

/**
 * linesReplace(lines, beginLineNo, endLineNo, newContentLines) => FileWholeLines
 * 在给定的行数组中，将从 beginLineNo 到 endLineNo 的行替换为 newContentLines，返回新的行数组
 * - 删除操作：如果 newContentLines 为空数组，则表示删除指定范围的行
 * - 插入操作：如果 beginLineNo 大于 endLineNo，则表示在 beginLineNo 位置插入 newContentLines（原先位于 beginLineNo 的行及之后的行会向后移动）
 * @deprecated 使用 replaceContent 代替
 */
export function innerReplace(content: FileContent,
                             beginLineNo: ContentLineNumber,
                             endLineNo: ContentLineNumber,
                             newBlock?: string[]): FileContent {
  const beginIndex = beginLineNo - 1;
  const endIndex = endLineNo - 1;
  const before = content.slice(0, beginIndex);
  const after = content.slice(endIndex + 1);

  if (!newBlock || newBlock.length === 0) {
    // 删除操作
    return [...before, ...after] as FileContent;
  } else if (beginLineNo > endLineNo) {
    // 插入操作
    return [...before, ...newBlock, ...after] as FileContent;
  } else {
    // 替换或插入操作
    return [...before, ...newBlock, ...after] as FileContent;
  }
}
