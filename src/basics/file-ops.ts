import {generateEntityTrashPath, getEntityFilePath, getJourneyFilePath, getMetaFilePath} from "../runtime.ts";
import shell from "shelljs";
import fs from "fs";
import {
  type FileAbsolutePath,
  FileType,
  type FileContent,
  type LibraryName,
  type ThingName
} from "@src/entities/editor/types.ts";
import {checks} from "@src/basics/utils.ts";

// 获取指定 Library 中特定 Thing 的绝对路径。
export function pathForFile(libraryName: LibraryName, fileType: FileType, thingName?: string): FileAbsolutePath {
  switch (fileType) {
  case FileType.FileTypeEntity:
    checks(!!thingName, `Entity 文件路径需要提供名称`);
    return getEntityFilePath(libraryName, thingName);
  case FileType.FileTypeJourney:
    checks(!!thingName, `Journey 文件路径需要提供名称`);
    return getJourneyFilePath(libraryName, thingName);
  case FileType.FileTypeMeta:
    return getMetaFilePath(libraryName);
  default:
    throw new Error(`未知的文件类型`);
  }
}

// 读指定 Library 中特定 Thing 的所有内容。
export function readFileContent(libraryName: LibraryName, fileType: FileType, name: ThingName): FileContent {
  const fullPath = pathForFile(libraryName, fileType, name);
  checks(shell.test('-f', fullPath), `无法找到文件: ${fullPath}`);
  const fileContent = fs.readFileSync(fullPath, 'utf-8');
  if (fileContent === '') {
    return [] as FileContent;
  }
  const content = fileContent.split('\n');
  return content as FileContent;
}

// 写指定 Library 中特定 Thing，覆盖其内容。
export function writeFileContent(libraryName: LibraryName, fileType: FileType, name: ThingName, content: FileContent): void {
  const fullPath = pathForFile(libraryName, fileType, name);
  fs.writeFileSync(fullPath, content.join('\n'), 'utf-8');
}

// 删除指定 Library 中特定 Thing 的文件，移动到回收站。
export function trashFile(libraryName: LibraryName, fileType: FileType, name: ThingName): void {
  const fullPath = pathForFile(libraryName, fileType, name);
  checks(shell.test('-f', fullPath), `无法找到文件: ${fullPath}`);
  const filePathInTrash = generateEntityTrashPath(libraryName, name);
  shell.mv(fullPath, filePathInTrash);
}

// 创建指定 Library 中特定 Thing 的文件，内容为 content；如果文件已存在则失败。
export function createFile(libraryName: LibraryName, fileType: FileType, name: ThingName, content: FileContent): void {
  const fullPath = pathForFile(libraryName, fileType, name);
  checks(!shell.test('-e', fullPath), `文件已存在，无法创建: ${fullPath}`);
  writeFileContent(libraryName, fileType, name, content);
}

// 重命名指定 Library 中特定 Thing 的文件，从 oldName 改为 newName。
export function renameFile(libraryName: LibraryName, fileType: FileType, oldName: ThingName, newName: ThingName): void {
  const oldFullPath = pathForFile(libraryName, fileType, oldName);
  const newFullPath = pathForFile(libraryName, fileType, newName);
  checks(shell.test('-f', oldFullPath), `无法找到源文件: ${oldFullPath}`);
  checks(!shell.test('-e', newFullPath), `目标文件已存在，无法重命名: ${newFullPath}`);
  shell.mv(oldFullPath, newFullPath);
}

// 检查指定 Library 中特定 Thing 的文件是否存在。
export function checkFileExists(libraryName: LibraryName, fileType: FileType, name: ThingName): boolean {
  const fullPath = pathForFile(libraryName, fileType, name);
  return shell.test('-f', fullPath);
}
