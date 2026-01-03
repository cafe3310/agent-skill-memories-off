import {
  type ContentLineExact,
  type ContentLocator,
  FileType,
  type FileContent,
  type LibraryName,
  type ContentLineNumber,
  type ThingName,
  type HeadingGlob, type Heading
} from "@src/entities/editor/types.ts";
import {readFileContent, writeFileContent} from "@src/basics/file-ops.ts";
import {getToc, matchToc, matchHeadingNoThrow} from "./toc.ts";
import {linesMatchContent, linesReplace, linesVerifyBeginEnd} from "./lines.ts";
import {checks} from "@src/basics/utils.ts";

export type Section = {
  heading: Heading;
  content: string[];
};

export function splitFileIntoSections(libraryName: LibraryName, fileType: FileType, name: ThingName): Section[] {
  const toc = getToc(libraryName, fileType, name);
  const sections: Section[] = [];

  for (const heading of toc) {
    const content = readSectionContent(libraryName, fileType, name, heading.text) ?? [];
    sections.push({heading, content });
  }

  return sections;
}


export function readSectionContent(libraryName: LibraryName, fileType: FileType, name: ThingName, tocGlob: HeadingGlob): string[] | null {
  const lines = readFileContent(libraryName, fileType, name);
  const tocList = getToc(libraryName, fileType, name);
  const matchedTocs = matchHeadingNoThrow(libraryName, fileType, name, tocGlob);

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
  let updatedLines: FileContent = [];
  if (oldContent.type === 'NumbersAndLines') {
    linesVerifyBeginEnd(lines, oldContent.beginLineNumber, oldContent.endLineNumber, oldContent.beginContentLine, oldContent.endContentLine);
    updatedLines = linesReplace(lines, oldContent.beginLineNumber, oldContent.endLineNumber, newContent);
  } else if (oldContent.type === 'Lines') {
    const beginLineNo = linesMatchContent(lines, oldContent.contentLines);
    const endLineNo = beginLineNo + oldContent.contentLines.length - 1;
    updatedLines = linesReplace(lines, beginLineNo, endLineNo, newContent);
  }
  checks(updatedLines && updatedLines.length > 0, `替换逻辑未执行，原因未知。`);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function replaceInToc(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, oldContent: ContentLocator, newContent: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc(libraryName, fileType, name);
  const matchedToc = matchToc(libraryName, fileType, name, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  let beginLineNo: ContentLineNumber;
  let endLineNo: ContentLineNumber;
  if (oldContent.type === 'NumbersAndLines') {
    linesVerifyBeginEnd(
      lines,
      oldContent.beginLineNumber,
      oldContent.endLineNumber,
      oldContent.beginContentLine,
      oldContent.endContentLine,
      sectionStartLineNumber,
      sectionEndLineNumber
    );
    beginLineNo = oldContent.beginLineNumber;
    endLineNo = oldContent.endLineNumber;
  } else if (oldContent.type === 'Lines') {
    beginLineNo = linesMatchContent(
      lines,
      oldContent.contentLines,
      sectionStartLineNumber,
      sectionEndLineNumber
    );
    endLineNo = beginLineNo + oldContent.contentLines.length - 1;
  } else {
    throw new Error(`未知的 oldContent 类型`);
  }

  const updatedLines = linesReplace(lines, beginLineNo, endLineNo, newContent);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function insertAfter(libraryName: LibraryName, fileType: FileType, name: ThingName, content: ContentLineExact[], afterContent: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const afterLineNo = linesMatchContent(lines, afterContent);
  const updatedLines = linesReplace(
    lines,
    afterLineNo,
    afterLineNo + afterContent.length - 1,
    [...afterContent, ...content]
  );
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function insertInTocAfter(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, content: ContentLineExact[], afterContent: ContentLineExact[]): void {

  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc(libraryName, fileType, name);
  const matchedToc = matchToc(libraryName, fileType, name, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const afterLineNo = linesMatchContent(
    lines,
    afterContent,
    sectionStartLineNumber,
    sectionEndLineNumber
  );

  const updatedLines = linesReplace(
    lines,
    afterLineNo,
    afterLineNo + afterContent.length - 1,
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

  const tocList = getToc(libraryName, fileType, name);
  const matchedToc = matchToc(libraryName, fileType, name, toc);
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
  const beginLineNo = linesMatchContent(lines, content);
  const endLineNo = beginLineNo + content.length - 1;
  const updatedLines = linesReplace(lines, beginLineNo, endLineNo, []);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function deleteInToc(libraryName: LibraryName, fileType: FileType, name: ThingName, toc: HeadingGlob, content: ContentLineExact[]): void {
  const lines = readFileContent(libraryName, fileType, name);

  const tocList = getToc(libraryName, fileType, name);
  const matchedToc = matchToc(libraryName, fileType, name, toc);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];
  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const beginLineNo = linesMatchContent(
    lines,
    content,
    sectionStartLineNumber,
    sectionEndLineNumber
  );
  const endLineNo = beginLineNo + content.length - 1;

  const updatedLines = linesReplace(lines, beginLineNo, endLineNo, []);
  writeFileContent(libraryName, fileType, name, updatedLines);
}

export function replaceSection(libraryName: LibraryName, fileType: FileType, name: ThingName, oldTocGlob: HeadingGlob, newHeading: string, newBodyContent: string[]): void {
  const lines = readFileContent(libraryName, fileType, name);
  const tocList = getToc(libraryName, fileType, name);
  const matchedToc = matchToc(libraryName, fileType, name, oldTocGlob);
  const tocLineNumber = matchedToc.lineNumber;

  const tocIndex = tocList.findIndex(item => item.lineNumber === tocLineNumber);
  const nextToc = tocList[tocIndex + 1];

  const sectionStartLineNumber: ContentLineNumber = tocLineNumber;
  const sectionEndLineNumber: ContentLineNumber = nextToc ? nextToc.lineNumber - 1 : lines.length;

  const newSectionLines = [newHeading, ...newBodyContent];
  const updatedLines = linesReplace(lines, sectionStartLineNumber, sectionEndLineNumber, newSectionLines);

  writeFileContent(libraryName, fileType, name, updatedLines);
}
