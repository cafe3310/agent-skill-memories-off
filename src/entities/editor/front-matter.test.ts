import {describe, test, expect, spyOn, beforeEach, type Mock} from 'bun:test';
import '@src/tests/setup';
import {
  type FileContent,
  FileType,
  type FrontMatter,
  FrontMatterPresetKeys,
  type LibraryName,
  type ThingName
} from "@src/entities/editor/types.ts";
import {
  locateFrontMatter,
  mergeFrontMatter,
  readFrontMatter,
  writeFrontMatter
} from "@src/entities/editor/front-matter.ts";
import shell from "shelljs";
import fs from "fs";
import * as mockSetup from "@src/tests/setup";

const MOCK_LIBRARY_NAME: LibraryName = mockSetup.MOCK_LIBRARY_NAME;
const MOCK_ENTITY_NAME: ThingName = mockSetup.MOCK_ENTITY_NAME;
const MOCK_FILE_CONTENT: FileContent = mockSetup.MOCK_FILE_CONTENT_1;

describe('locateFrontMatter', () => {

  // mock: shell.test，在不真实检查文件是否存在的情况下控制「文件是否存在」
  const shellTestSpy = spyOn(shell, 'test') as Mock<(...args: unknown[]) => boolean>;

  // mock: fs.readFileSync，在不真实读文件的情况下控制「读出内容」
  const readSpy = spyOn(fs, 'readFileSync') as Mock<(...args: unknown[]) => string>;

  // mock: fs.writeFileSync，在不真实写文件的情况下控制「写入内容」
  const writeSpy = spyOn(fs, 'writeFileSync') as Mock<(...args: unknown[]) => void>;

  beforeEach(() => {
    shellTestSpy.mockClear();
    readSpy.mockClear();
    writeSpy.mockClear();
  });

  test('should return null if no front matter exists', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['# A heading', 'Some content.'].join('\n'));
    expect(locateFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toBeNull();
  });

  test('should return null if front matter is not closed', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'key: value'].join('\n'));
    expect(locateFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toBeNull();
  });

  test('should return null for empty file', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue('');
    expect(locateFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toBeNull();
  });

  test('should locate front matter correctly', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'key: value', 'another: item', '---', '# Body'].join('\n'));
    const result = locateFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    });
    expect(result).toEqual({
      target: {
        library: MOCK_LIBRARY_NAME,
        type: FileType.FileTypeEntity,
        name: MOCK_ENTITY_NAME,
      },
      origin: 'frontmatter',
      beginLineNumber: 1,
      endLineNumber: 4,
      beginContentLine: '---',
      endContentLine: '---',
    });
  });
});

describe('readFrontMatter', () => {


  // mock: shell.test，在不真实检查文件是否存在的情况下控制「文件是否存在」
  const shellTestSpy = spyOn(shell, 'test') as Mock<(...args: unknown[]) => boolean>;

  // mock: fs.readFileSync，在不真实读文件的情况下控制「读出内容」
  const readSpy = spyOn(fs, 'readFileSync') as Mock<(...args: unknown[]) => string>;

  // mock: fs.writeFileSync，在不真实写文件的情况下控制「写入内容」
  const writeSpy = spyOn(fs, 'writeFileSync') as Mock<(...args: unknown[]) => void>;

  beforeEach(() => {
    shellTestSpy.mockClear();
    readSpy.mockClear();
    writeSpy.mockClear();
  });

  test('should return empty array if no front matter exists', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['# A heading', 'Some content.'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([]);
  });

  test('should read front matter key-value pairs correctly', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'key1: value1', 'key2: value2', '---', '# Body'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([
      { name: 'key1', value: 'value1' },
      { name: 'key2', value: 'value2' },
    ]);
  });

  test('should handle empty front matter block', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', '---', '# Content'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([]);
  });

  test('should handle keys without values', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'key-only:', '---', '# Content'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([{ name: 'key-only', value: '' }]);
  });

  test('should handle keys without values and colon', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'key-only', '---', '# Content'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([{ name: 'key-only', value: '' }]);
  });

  test('should handle multiple colon correctly', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'complex-key: value: with: colons', 'another-key: another:value', '---', '# Content'].join('\n'));
    expect(readFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    })).toEqual([
      { name: 'complex-key', value: 'value: with: colons' },
      { name: 'another-key', value: 'another:value' },
    ]);
  });
});

describe('writeFrontMatter', () => {


  // mock: shell.test，在不真实检查文件是否存在的情况下控制「文件是否存在」
  const shellTestSpy = spyOn(shell, 'test') as Mock<(...args: unknown[]) => boolean>;

  // mock: fs.readFileSync，在不真实读文件的情况下控制「读出内容」
  const readSpy = spyOn(fs, 'readFileSync') as Mock<(...args: unknown[]) => string>;

  // mock: fs.writeFileSync，在不真实写文件的情况下控制「写入内容」
  const writeSpy = spyOn(fs, 'writeFileSync') as Mock<(...args: unknown[]) => void>;

  beforeEach(() => {
    shellTestSpy.mockClear();
    readSpy.mockClear();
    writeSpy.mockClear();
  });

  test('should add front matter to a file that does not have it', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['# Title', 'This is the content.'].join('\n'));
    const newFrontMatter: FrontMatter = [{ name: 'status', value: 'draft' }];
    writeFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    }, newFrontMatter);
    expect(writeSpy).toHaveBeenCalledWith(
      expect.anything(),
      ['---', 'status: draft', '---', '# Title', 'This is the content.'].join('\n'),
      'utf-8'
    );
  });

  test('should overwrite existing front matter', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'status: published', '---', '# Title'].join('\n'));
    const newFrontMatter: FrontMatter = [{ name: 'status', value: 'archived' }, {name: 'author', value: 'sipan'}];
    writeFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    }, newFrontMatter);
    expect(writeSpy).toHaveBeenCalledWith(
      expect.anything(),
      ['---', 'status: archived', 'author: sipan', '---', '# Title'].join('\n'),
      'utf-8'
    );
  });

  test('should write to an empty file', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue('');
    const newFrontMatter: FrontMatter = [{ name: 'type', value: 'note' }];
    writeFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    }, newFrontMatter);
    expect(writeSpy).toHaveBeenCalledWith(
      expect.anything(),
      ['---', 'type: note', '---'].join('\n'),
      'utf-8'
    );
  });

  test('should effectively remove front matter when writing an empty array', () => {
    shellTestSpy.mockReturnValue(true);
    readSpy.mockReturnValue(['---', 'status: published', '---', '# Title'].join('\n'));
    writeFrontMatter({
      library: MOCK_LIBRARY_NAME,
      type: FileType.FileTypeEntity,
      name: MOCK_ENTITY_NAME,
    }, []);
    expect(writeSpy).toHaveBeenCalledWith(
      expect.anything(),
      ['---', '---', '# Title'].join('\n'),
      'utf-8'
    );
  });
});

describe('mergeFrontmatter', () => {
  test('should merge new keys from source', () => {
    const target: FrontMatter = [{name: 'key1', value: 'value1'}];
    const source: FrontMatter = [{name: 'key2', value: 'value2'}];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(2);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key1: value1');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key2: value2');
  });

  test('should not change existing keys with same values', () => {
    const target: FrontMatter = [{name: 'key1', value: 'value1'}];
    const source: FrontMatter = [{name: 'key1', value: 'value1'}];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(1);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key1: value1');
  });

  test('should merge existing keys with different values', () => {
    const target: FrontMatter = [{name: 'key1', value: 'value1'}];
    const source: FrontMatter = [{name: 'key1', value: 'value2'}];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(1);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key1: value1, value2');
  });

  test('should handle aliases correctly (merge and deduplicate)', () => {
    const target: FrontMatter = [{name: FrontMatterPresetKeys.Aliases, value: 'alias1, alias2'}];
    const source: FrontMatter = [{name: FrontMatterPresetKeys.Aliases, value: 'alias2, alias3'}];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(1);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain(`${FrontMatterPresetKeys.Aliases}: alias1, alias2, alias3`);
  });

  test('should handle a complex mix of cases', () => {
    const target: FrontMatter = [
      {name: 'type', value: 'concept'},
      {name: 'status', value: 'draft'},
      {name: FrontMatterPresetKeys.Aliases, value: 'T1, T2'},
    ];
    const source: FrontMatter = [
      {name: 'type', value: 'idea'},
      {name: 'status', value: 'draft'},
      {name: 'habitat', value: 'jungle'},
      {name: FrontMatterPresetKeys.Aliases, value: 'T2, S1'},
    ];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(4);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('type: concept, idea');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('status: draft');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('habitat: jungle');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain(`${FrontMatterPresetKeys.Aliases}: T1, T2, S1`);
  });

  test('should handle empty target', () => {
    const target: FrontMatter = [];
    const source: FrontMatter = [
      {name: 'key1', value: 'value1'},
      {name: 'key2', value: 'value2'},
    ];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(2);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key1: value1');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key2: value2');
  });

  test('should handle empty source', () => {
    const target: FrontMatter = [{name: 'key1', value: 'value1'}, {name: 'key2', value: 'value2'}];
    const source: FrontMatter = [];
    const result = mergeFrontMatter(target, source);
    expect(result).toHaveLength(2);
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key1: value1');
    expect(result.map(x => `${x.name}: ${x.value}`)).toContain('key2: value2');
  });
});
