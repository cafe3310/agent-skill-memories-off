import {describe, expect, it, type Mock, spyOn, beforeEach, afterEach} from 'bun:test';
import '@src/tests/setup';

import fs from 'fs';
import {matchHeadingInToc, matchHeadingInTocNoThrow, getToc} from "./toc.ts";
import shell from "shelljs";
import * as mockSetup from "@src/tests/setup";
import {FileType, type FileContent, type LibraryName, type ThingName} from "@src/entities/editor/types.ts";

const MOCK_LIBRARY_NAME: LibraryName = mockSetup.MOCK_LIBRARY_NAME;
const MOCK_ENTITY_NAME: ThingName = mockSetup.MOCK_ENTITY_NAME;
const MOCK_FILE_CONTENT_LINES: FileContent = mockSetup.MOCK_FILE_CONTENT_1;

describe('TOC operations', () => {
  const readSpy = spyOn(fs, 'readFileSync') as Mock<(...args: unknown[]) => string>;
  const shellTestSpy = spyOn(shell, 'test') as Mock<(...args: unknown[]) => boolean>;


  beforeEach(() => {
    readSpy.mockImplementation(() => MOCK_FILE_CONTENT_LINES.join('\n'));
    shellTestSpy.mockImplementation(() => true);
  });

  afterEach(() => {
    readSpy.mockClear();
    shellTestSpy.mockClear();
  })

  it('getTocList', () => {

    const toc = getToc({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME});

    expect(toc.length).toBe(4);

    expect(toc[0]!.text).toBe('# Welcome');
    expect(toc[0]!.lineNumber).toBe(1);

    expect(toc[1]!.text.startsWith('## Section 1')).toBe(true);
    expect(toc[1]!.lineNumber).toBe(6);

    expect(toc[2]!.text.startsWith('## Section 2')).toBe(true);
    expect(toc[2]!.lineNumber).toBe(12);

    expect(toc[3]!.text.startsWith('## Section 3')).toBe(true);
    expect(toc[3]!.lineNumber).toBe(15);
  });

  it('matchToc should find a unique TOC item', () => {
    const tocItem = matchHeadingInToc({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'Section 1: Details');
    expect(tocItem.lineNumber).toBe(6);
    expect(tocItem.text).toBe('## Section 1: Details');
  });

  it('matchToc should throw if TOC item not found', () => {
    expect(() => matchHeadingInToc({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'Non-Existent Section')).toThrowError();
  });

  it('matchToc should throw if TOC item is ambiguous', () => {
    // Create content where two different titles normalize to the same string
    const ambiguousTocLines = [
      '# Welcome',
      '## Section 1: Details', // normalizes to 'section 1 details'
      'Some content',
      '## section 1 (details)', // also normalizes to 'section 1 details'
    ] as FileContent;

    readSpy.mockImplementation(() => ambiguousTocLines.join('\n'));

    // Use the normalized string that causes ambiguity
    expect(() => matchHeadingInToc({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'section 1 details')).toThrow('发现多个与');

    // Restore the spy to the default mock implementation for subsequent tests
    readSpy.mockImplementation(() => MOCK_FILE_CONTENT_LINES.join('\n'));
  });

  it('matchTocNoThrow should return matches without throwing', () => {
    // Case 1: Unique match
    let matches = matchHeadingInTocNoThrow({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'Section 1: Details');
    expect(matches.length).toBe(1);
    expect(matches[0]!.lineNumber).toBe(6);

    // Case 2: No match
    matches = matchHeadingInTocNoThrow({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'Non-Existent Section');
    expect(matches.length).toBe(0);

    // Case 3: Ambiguous match
    const ambiguousTocLines = [
      '# Welcome',
      '## Section 1: Details',
      '## section 1 (details)',
    ] as FileContent;
    readSpy.mockImplementation(() => ambiguousTocLines.join('\n'));
    matches = matchHeadingInTocNoThrow({library: MOCK_LIBRARY_NAME, type: FileType.FileTypeEntity, name: MOCK_ENTITY_NAME}, 'section 1 details');
    expect(matches.length).toBe(2);

    // Restore spy
    readSpy.mockImplementation(() => MOCK_FILE_CONTENT_LINES.join('\n'));
  });
});
