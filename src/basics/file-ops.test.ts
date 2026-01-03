import {afterEach, describe, expect, it, type Mock, spyOn, beforeEach} from 'bun:test';
import '@src/tests/setup';
import {FileType, type FileContent, type LibraryName, type ThingName} from "@src/entities/editor/types.ts";
import shell from 'shelljs';
import fs from 'fs';
import * as mockSetup from "@src/tests/setup";
import {createFile, readFileContent} from "./file-ops.ts";

const MOCK_LIBRARY_NAME: LibraryName = mockSetup.MOCK_LIBRARY_NAME;
const MOCK_ENTITY_NAME: ThingName = mockSetup.MOCK_ENTITY_NAME;
const MOCK_FILE_CONTENT: FileContent = mockSetup.MOCK_FILE_CONTENT_1;

describe('file operations', () => {

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

  it('readFileContent - works', () => {

    // mock: 文件存在且可读出 MOCK_FILE_CONTENT 的内容
    shellTestSpy.mockImplementation(() => true);
    readSpy.mockImplementation(() => MOCK_FILE_CONTENT.join('\n'));

    const lines = readFileContent(MOCK_LIBRARY_NAME, FileType.FileTypeEntity, MOCK_ENTITY_NAME);
    expect(lines).toEqual(MOCK_FILE_CONTENT);
  });

  it('createFile - create file when file not exists', () => {

    // mock: 文件不存在
    shellTestSpy.mockImplementation(() => false); // Mock file does not exist

    const newContent: FileContent = ['new file content'] as FileContent;
    createFile(MOCK_LIBRARY_NAME, FileType.FileTypeEntity, 'new-file', newContent);
    expect(writeSpy).toHaveBeenCalledTimes(1);
    expect(writeSpy.mock.calls[0]![1]).toBe('new file content');
  });

  it('createFile - should throw when file exists', () => {

    // mock: 文件已存在
    shellTestSpy.mockImplementation(() => true);

    const newContent: FileContent = ['new file content'] as FileContent;
    expect(() => createFile(MOCK_LIBRARY_NAME, FileType.FileTypeEntity, 'existing-file', newContent)).toThrow('文件已存在，无法创建');
  });
});
