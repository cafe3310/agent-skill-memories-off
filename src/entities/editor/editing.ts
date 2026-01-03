import {
  type ContentLineExact,
  type ContentLineNumber,
  type ContentLocator,
  type FileContent,
  FileType,
  type Heading,
  type HeadingGlob,
  type LibraryName,
  type ThingName
} from "@src/entities/editor/types.ts";
import {readFileContent, writeFileContent} from "@src/basics/file-ops.ts";
import {getToc, matchHeadingNoThrow, matchToc} from "./toc.ts";
import {resolveContentLocator} from "./locator.ts";
import {checks} from "@src/basics/utils.ts";

export type Section = {
  heading: Heading;
  content: string[];
};

export function splitFileIntoSections(libraryName: LibraryName, fileType: FileType, name: ThingName): Section[] {
  const toc = getToc({ library: libraryName, type: fileType, name: name });
  const sections: Section[] = [];

  for (const heading of toc) {
    const content = readSectionContent(libraryName, fileType, name, heading.text) ?? [];
    sections.push({heading, content });
  }

  return sections;
}


export function readSectionContent(libraryName: LibraryName, fileType: FileType, name: ThingName, tocGlob: HeadingGlob): string[] | null {
  const lines = readFileContent(libraryName, fileType, name);
  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  const matchedTocs = matchHeadingNoThrow({library: libraryName, type: fileType, name: name}, tocGlob);

  // Only proceed if we find exactly one match
  if (matchedTocs.length !== 1) {
    return null;
  }
  const matchedToc = matchedTocs[0]!;
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];

  const sectionStartLineNumber: ContentLineNumber = tocLineNumber + 1; // Content starts after the heading
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  if (sectionStartLineNumber > sectionEndLineNumber) {
    return []; // Section has a heading but no content
  }

  return lines.slice(sectionStartLineNumber - 1, sectionEndLineNumber);
}

export function replace(libraryName: LibraryName, fileType: FileType, name: ThingName, oldContent: ContentLocator, newContent: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const resolved = resolveContentLocator({library: libraryName, type: fileType, name: name}, oldContent);
  const updatedLines: FileContent = linesReplace(lines, resolved.beginLineNumber, resolved.endLineNumber, newContent);
  checks(updatedLines && updatedLines.length > 0, `替换逻辑未执行，原因未知。`);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function replaceInToc(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, oldContent: ContentLocator, newContent: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  // args to obj: {library: libraryName, type: fileType, name: name}
  const matchedToc = matchToc({ library: libraryName, type: fileType, name: name }, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const resolved = resolveContentLocator({
    library: libraryName,
    type: fileType,
    name: name
  }, oldContent, {
    searchStartLine: sectionStartLineNumber,
    searchEndLine: sectionEndLineNumber
  });
  const beginLineNo = resolved.beginLineNumber;
  const endLineNo = resolved.endLineNumber;
  const updatedLines = linesReplace(lines, beginLineNo, endLineNo, newContent);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function insertAfter(libraryName: LibraryName, fileType: FileType, name: ThingName, content: ContentLineExact[], afterContent: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const resolved = resolveContentLocator({ library: libraryName, type: fileType, name: name }, {
    type: 'Lines',
    contentLines: afterContent
  });
  const updatedLines = linesReplace(
    lines,
    resolved.beginLineNumber,
    resolved.endLineNumber,
    [...afterContent, ...content]
  );
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function insertInTocAfter(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, content: ContentLineExact[], afterContent: ContentLineExact[]): void {

  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  const matchedToc = matchToc({ library: libraryName, type: fileType, name: name }, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const resolved = resolveContentLocator({
    library: libraryName,
    type: fileType,
    name: name
  }, {
    type: 'Lines',
    contentLines: afterContent
  }, {
    searchStartLine: sectionStartLineNumber,
    searchEndLine: sectionEndLineNumber
  });

  const updatedLines = linesReplace(
    lines,
    resolved.beginLineNumber,
    resolved.endLineNumber,
    [...afterContent, ...content]
  );

  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function addContentToThing(libraryName: LibraryName, fileType: FileType, name: ThingName, content: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const updatedLines = [...lines, ...content] as FileContent;
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function addContentToSection(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, content: ContentLineExact[]): void {

  const lines = readFileContent(libraryName, fileType, name);

  // const tocList = getToc(libraryName, fileType, name);
  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  const matchedToc = matchToc({ library: libraryName, type: fileType, name: name }, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const insertLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber : (lines.length + 1);

  let updatedLines: FileContent;
  if (insertLineNumber <= lines.length) {
    const targetLineContent = lines[insertLineNumber - 1];
    updatedLines = linesReplace(
      lines,
      insertLineNumber,
      insertLineNumber,
      [...content, targetLineContent ?? '']
    );
    writeFileContent(libraryName, fileType, name, updatedLines);
  } else {
    updatedLines = [...lines, ...content] as FileContent;
    writeFileContent(libraryName, fileType, name, updatedLines);
  }
}

export function deleteContent(libraryName: LibraryName, fileType: FileType, name: ThingName, content: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const resolved = resolveContentLocator({ library: libraryName, type: fileType, name: name }, { type: 'Lines', contentLines: content });
  const updatedLines = linesReplace(lines, resolved.beginLineNumber, resolved.endLineNumber, []);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function deleteInToc(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, content: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  const matchedToc = matchToc({ library: libraryName, type: fileType, name: name }, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const resolved = resolveContentLocator({
    library: libraryName,
    type: fileType,
    name: name
  }, {
    type: 'Lines',
    contentLines: content
  }, {
    searchStartLine: sectionStartLineNumber,
    searchEndLine: sectionEndLineNumber
  });
  const updatedLines = linesReplace(lines, resolved.beginLineNumber, resolved.endLineNumber, []);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function replaceSection(libraryName: LibraryName, fileType: FileType, name: ThingName, oldTocGlob: HeadingGlob, newHeading: string, newBodyContent: string[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const tocList = getToc({ library: libraryName, type: fileType, name: name });
  const matchedToc = matchToc({ library: libraryName, type: fileType, name: name }, oldTocGlob);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];

  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const newSectionLines = [newHeading, ...newBodyContent];
  const updatedLines = linesReplace(lines, sectionStartLineNumber, sectionEndLineNumber, newSectionLines);

  writeFileContent(libraryName, fileType, name, updatedLines);
}

// linesReplace(lines, beginLineNo, endLineNo, newContentLines) => FileWholeLines
// 在给定的行数组中，将从 beginLineNo 到 endLineNo 的行替换为 newContentLines，返回新的行数组。
export function linesReplace(lines: FileContent,
                             beginLineNo: ContentLineNumber, endLineNo: ContentLineNumber,
                             newContentLines: string[]): FileContent {
  const beginIndex = beginLineNo - 1;
  const endIndex = endLineNo - 1;
  const before = lines.slice(0, beginIndex);
  const after = lines.slice(endIndex + 1);

  if (newContentLines.length === 0) {
    // 删除操作
    return [...before, ...after] as FileContent;
  } else {
    // 替换或插入操作
    return [...before, ...newContentLines, ...after] as FileContent;
  }
}
