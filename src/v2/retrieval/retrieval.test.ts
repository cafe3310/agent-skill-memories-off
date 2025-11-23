import '../../test/setup';
import {describe, it, expect, spyOn, beforeEach, afterEach} from 'bun:test';
import shell from 'shelljs';
import * as runtime from '../runtime';
import {
  findEntityByNameGlob,
  findEntityByFrontMatterRegex,
  findEntityByNonFrontMatterRegex,
  findRelations // Import the new function
} from './retrieval';
import type {LibraryName} from '../../typings';
import * as fileOps from '../editor/file-ops';
import {FileType} from "../../typings.ts";

describe('retrieval functions', () => {
  const MOCK_LIBRARY_NAME = 'test-library' as LibraryName;
  const MOCK_ENTITY_DIR = '/test/entities';

  const lsSpy = spyOn(shell, 'ls');
  const grepSpy = spyOn(shell, 'grep');
  const getEntityDirPathSpy = spyOn(runtime, 'getEntityDirPath');
  const readFileLinesSpy = spyOn(fileOps, 'readFileLines');

  beforeEach(() => {
    lsSpy.mockClear();
    grepSpy.mockClear();
    getEntityDirPathSpy.mockClear();
    readFileLinesSpy.mockClear();
    // Mock getEntityDirPath to avoid dependency on runtime environment
    getEntityDirPathSpy.mockReturnValue(MOCK_ENTITY_DIR);
  });

  afterEach(() => {
    lsSpy.mockClear();
    grepSpy.mockClear();
    getEntityDirPathSpy.mockClear();
    readFileLinesSpy.mockClear();
  })

  it('should return a list of entity names matching the glob pattern', () => {
    const mockFiles = [`${MOCK_ENTITY_DIR}/file1.md`, `${MOCK_ENTITY_DIR}/file2.md`];
    lsSpy.mockReturnValue(mockFiles as any);

    const result = findEntityByNameGlob(MOCK_LIBRARY_NAME, '*.md');

    expect(result).toEqual(['file1', 'file2']);
    expect(getEntityDirPathSpy).toHaveBeenCalledWith(MOCK_LIBRARY_NAME);
    expect(lsSpy).toHaveBeenCalledWith(`${MOCK_ENTITY_DIR}/*.md`);
  });

  it('should find entities with content matching the regex', () => {
    const mockFiles = [`${MOCK_ENTITY_DIR}/file1.md`, `${MOCK_ENTITY_DIR}/file2.md`];
    grepSpy.mockReturnValue({ stdout: mockFiles.join('\n') } as any);

    readFileLinesSpy
      .mockReturnValueOnce(['---', 'prop: value', '---', 'some content with pattern here'].map(l => l as any))
      .mockReturnValueOnce(['no frontmatter', 'another pattern line'].map(l => l as any));

    const result = findEntityByNonFrontMatterRegex(MOCK_LIBRARY_NAME, '*.md', 'pattern');

    expect(result).toEqual([
      { name: 'file1', line: 'some content with pattern here' },
      { name: 'file2', line: 'another pattern line' },
    ]);
    expect(grepSpy).toHaveBeenCalledWith('-l', 'pattern', `${MOCK_ENTITY_DIR}/*.md`);
    expect(readFileLinesSpy).toHaveBeenCalledWith(MOCK_LIBRARY_NAME, FileType.FileTypeEntity, 'file1');
    expect(readFileLinesSpy).toHaveBeenCalledWith(MOCK_LIBRARY_NAME, FileType.FileTypeEntity, 'file2');
  });

  it('should find entities with front matter matching the regex', () => {
    const mockFiles = [`${MOCK_ENTITY_DIR}/file1.md`];
    grepSpy.mockReturnValue({ stdout: mockFiles.join('\n') } as any);

    readFileLinesSpy
      .mockReturnValueOnce(['---', 'prop: value with pattern', '---', 'some content'].map(l => l as any));

    const result = findEntityByFrontMatterRegex(MOCK_LIBRARY_NAME, '*.md', 'pattern');

    expect(result).toEqual([
      { name: 'file1', line: 'prop: value with pattern' },
    ]);
    expect(grepSpy).toHaveBeenCalledWith('-l', 'pattern', `${MOCK_ENTITY_DIR}/*.md`);
    expect(readFileLinesSpy).toHaveBeenCalledWith(mockFiles[0], FileType.FileTypeEntity, 'file1');
  });

  it('should find relations based on filters', () => {
    // Mock entities with relations
    lsSpy.mockReturnValueOnce([
      `${MOCK_ENTITY_DIR}/person1.md`,
      `${MOCK_ENTITY_DIR}/person2.md`,
      `${MOCK_ENTITY_DIR}/company1.md`,
    ] as any);

    // Mock file content for person1.md
    readFileLinesSpy.mockImplementation((libraryName, fileType, thingName) => {
      if (thingName === 'person1') {
        return [
          '---',
          'entity type: Person',
          'relation as works_for: company1',
          'relation as knows: person2',
          '---',
          '# Person1',
        ] as any;
      }
      if (thingName === 'person2') {
        return [
          '---',
          'entity type: Person',
          'relation as works_for: company1',
          '---',
          '# Person2',
        ] as any;
      }
      if (thingName === 'company1') {
        return [
          '---',
          'entity type: Company',
          '---',
          '# Company1',
        ] as any;
      }
      return [] as any; // Default empty
    });

    // Test 1: Find all relations
    let result = findRelations(MOCK_LIBRARY_NAME, undefined, undefined); // Assuming findRelations takes these args
    expect(result).toEqual([
      { source: 'person1', verb: 'works_for', target: 'company1' },
      { source: 'person1', verb: 'knows', target: 'person2' },
      { source: 'person2', verb: 'works_for', target: 'company1' },
    ]);

    // Test 2: Filter by toEntity
    result = findRelations(MOCK_LIBRARY_NAME, 'company1', undefined);
    expect(result).toEqual([
      { source: 'person1', verb: 'works_for', target: 'company1' },
      { source: 'person2', verb: 'works_for', target: 'company1' },
    ]);

    // Test 3: Filter by relationType
    result = findRelations(MOCK_LIBRARY_NAME, undefined, 'knows');
    expect(result).toEqual([
      { source: 'person1', verb: 'knows', target: 'person2' },
    ]);

    // Test 4: Filter by both
    result = findRelations(MOCK_LIBRARY_NAME, 'person2', 'knows');
    expect(result).toEqual([
      { source: 'person1', verb: 'knows', target: 'person2' },
    ]);

    // Test 5: No matching relations
    result = findRelations(MOCK_LIBRARY_NAME, 'nonexistent', 'type');
    expect(result).toEqual([]);
  });
});
