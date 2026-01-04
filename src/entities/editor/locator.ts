import type {
  ContentLineNumber,
  ContentLocator,
  FileContent,
  ResolvedContentLocator,
  ThingLocator
} from "@src/entities/editor/types.ts";
import {checks} from "@src/basics/utils.ts";
import {readFileContent} from "@src/basics/file-ops.ts";

// 检查 locator 是否在 target 中可唯一定位内容，如果是，返回具备具体行号的 ResolvedContentLocator，否则抛出错误。
export function resolveContentLocator(target: ThingLocator, locator: ContentLocator, targetRegion?: {
  searchStartLine: ContentLineNumber;
  searchEndLine: ContentLineNumber;
}): ResolvedContentLocator {

  // 先读目标内容
  const content = readFileContent(target);

  // 尝试匹配
  if (locator.type === 'NumbersAndLines') {
    linesVerifyBeginEnd(content, locator.beginLineNumber, locator.endLineNumber, locator.beginContentLine, locator.endContentLine, targetRegion?.searchStartLine, targetRegion?.searchEndLine);
    return {
      target: target,
      origin: locator,
      beginLineNumber: locator.beginLineNumber,
      endLineNumber: locator.endLineNumber,
      beginContentLine: locator.beginContentLine,
      endContentLine: locator.endContentLine,
    };
  } else if (locator.type === 'Lines') {
    const result = linesMatchContent(content, locator.contentLines, targetRegion?.searchStartLine, targetRegion?.searchEndLine);
    return {
      target: target,
      origin: locator,
      beginLineNumber: result,
      endLineNumber: result + locator.contentLines.length - 1,
      beginContentLine: locator.contentLines[0]!,
      endContentLine: locator.contentLines[locator.contentLines.length - 1]!,
    };
  } else {
    throw new Error(`不支持的 ContentLocator：${JSON.stringify(locator)}`);
  }
}

/**
 * linesVerifyBeginEnd(lines, beginLineNo, endLineNo, beginLine, endLine, searchStartLine?, searchEndLine?) => void
 * 检查给定的行数组中，从 beginLineNo 到 endLineNo 的内容，开头和结尾与 beginLine 和 endLine 匹配。
 * 如果设置了 searchStartLine 和 searchEndLine，则只在该范围内进行检查。
 * 若不匹配，则抛出错误。
 * @deprecated: 用 resolveContentLocator 替代
 */
export function linesVerifyBeginEnd(content: FileContent,
                                    beginLineNo: ContentLineNumber, endLineNo: ContentLineNumber,
                                    beginLine: string, endLine: string,
                                    searchStartLine?: ContentLineNumber, searchEndLine?: ContentLineNumber): void {
  const startIndex = (searchStartLine ? searchStartLine - 1 : 0);
  const endIndex = (searchEndLine ? searchEndLine - 1 : content.length - 1);
  checks(beginLineNo - 1 >= startIndex && endLineNo - 1 <= endIndex, `指定的行号范围超出搜索范围。`);
  const actualBeginLine = content[beginLineNo - 1];
  checks(actualBeginLine === beginLine, `起始行在第 ${beginLineNo} 行不匹配。`);
  const actualEndLine = content[endLineNo - 1];
  checks(actualEndLine === endLine, `结束行在第 ${endLineNo} 行不匹配。`);
}

/**
 * linesMatchContent(lines, contentLines, searchStartLine?, searchEndLine?) => LineNumber
 * 在给定的行数组中，检查是否存在与 contentLines 完全匹配的连续行段，且是唯一的匹配。
 * 如果设置了 searchStartLine 和 searchEndLine，则只在该范围内进行检查。
 * 若找到唯一匹配，返回起始行号（从 1 开始计数）；否则抛出异常。
 * @deprecated: 用 resolveContentLocator 替代
 */
export function linesMatchContent(lines: FileContent,
                                  contentLines: string[],
                                  searchStartLine?: ContentLineNumber, searchEndLine?: ContentLineNumber): ContentLineNumber {
  const startIndex = (searchStartLine ? searchStartLine - 1 : 0);
  const endIndex = (searchEndLine ? searchEndLine - 1 : lines.length - 1);
  const matches: ContentLineNumber[] = [];
  for (let i = startIndex; i <= endIndex - contentLines.length + 1; i++) {
    const segment = lines.slice(i, i + contentLines.length);
    if (segment.join('\n') === contentLines.join('\n')) {
      matches.push(i + 1); // 转换为从 1 开始计数的行号
    }
  }
  checks(matches.length !== 0, `未找到匹配的内容块。`);
  checks(matches.length === 1, `发现多个匹配的内容块，请提供更精确的定位。`);
  return matches[0]!;
}

