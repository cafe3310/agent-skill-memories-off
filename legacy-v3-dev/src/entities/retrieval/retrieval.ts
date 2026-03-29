// import shell from 'shelljs';
// import path from 'path';
// import {locateFrontMatter, readFrontMatter} from "../editor/front-matter.ts";
// import {
//   type ContentLineExact,
//   FileType,
//   type FrontMatterLine,
//   FrontMatterPresetKeys,
//   type LibraryName, type ContentLineNumber,
//   type ThingName
// } from "@src/entities/editor/types.ts";
// import {getEntityDirPath, getThingNameFromPath} from "@src/runtime.ts";
// import {globToRegex} from "@src/basics/utils.ts";
// import {readFileContent} from "@src/basics/file-ops.ts";
//
//
// export function listAllEntityTypesWithCounts(libraryName: LibraryName): { type: string, count: number }[] {
//   const entityDirPath = getEntityDirPath(libraryName);
//   const files = shell.ls(path.join(entityDirPath, '*.md'));
//   const entityTypeCounts: Record<string, number> = {};
//
//   for (const filePath of files) {
//     const thingName = getThingNameFromPath(filePath, FileType.FileTypeEntity);
//     const frontMatter = readFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: thingName});
//     if (!frontMatter) {
//       continue;
//     }
//
//     const entityTypeLine = frontMatter.find(line => line.startsWith(`${FrontMatterPresetKeys.EntityType}:`));
//     if (entityTypeLine) {
//       const entityType = entityTypeLine.substring(FrontMatterPresetKeys.EntityType.length + 1).trim();
//       entityTypeCounts[entityType] = (entityTypeCounts[entityType] ?? 0) + 1;
//     }
//   }
//
//   return Object.entries(entityTypeCounts)
//     .map(([type, count]) => ({type, count}))
//     .sort((a, b) => b.count - a.count);
// }
//
// export function findEntitiesByMetadataQuery(libraryName: LibraryName, metadataQuery: Record<string, string | boolean>): Record<ThingName, FrontMatterLine[]> {
//   const entityDirPath = getEntityDirPath(libraryName);
//   const files = shell.ls(path.join(entityDirPath, '*.md'));
//   const matchingEntities: Record<ThingName, FrontMatterLine[]> = {};
//
//   for (const filePath of files) {
//     const thingName = getThingNameFromPath(filePath, FileType.FileTypeEntity);
//     const frontMatter = readFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: thingName});
//     if (!frontMatter || frontMatter.length === 0) {
//       continue;
//     }
//
//     const matchedLines: FrontMatterLine[] = [];
//     let isMatch = true;
//     for (const key in metadataQuery) {
//       const queryValue = metadataQuery[key];
//       const frontMatterLine = frontMatter.find(line => line.startsWith(`${key}:`));
//
//       if (!frontMatterLine) {
//         isMatch = false;
//         break;
//       }
//
//       const value = frontMatterLine.substring(key.length + 1).trim();
//       if (typeof queryValue === 'string') {
//         const regex = new RegExp(globToRegex(queryValue));
//         if (regex.test(value)) {
//           matchedLines.push(frontMatterLine as FrontMatterLine);
//         } else {
//           isMatch = false;
//           break;
//         }
//       } else if (typeof queryValue === 'boolean') {
//         if (value.toLowerCase() === queryValue.toString()) {
//           matchedLines.push(frontMatterLine as FrontMatterLine);
//         } else {
//           isMatch = false;
//           break;
//         }
//       }
//     }
//
//     if (isMatch && matchedLines.length > 0) {
//       matchingEntities[thingName] = matchedLines;
//     }
//   }
//
//   return matchingEntities;
// }
//
//
// export function findEntityByNameGlob(libraryName: LibraryName, globPattern: string): ThingName[] {
//   const entityDirPath = getEntityDirPath(libraryName);
//   const fullGlobPath = path.join(entityDirPath, globPattern);
//   const files = shell.ls(fullGlobPath);
//   return files.map(filePath => getThingNameFromPath(filePath, FileType.FileTypeEntity));
// }
//
// export function findEntityByNonFrontMatterRegex(libraryName: LibraryName, fileGlobPattern: string, contentRegexPattern: string): {
//   name: ThingName,
//   line: ContentLineExact
// }[] {
//   // 先 grep 内容
//   const entityDirPath = getEntityDirPath(libraryName);
//   const fullGlobPath = path.join(entityDirPath, fileGlobPattern);
//   const grepResult = shell.grep('-l', contentRegexPattern, fullGlobPath);
//   const matchedFiles = grepResult.stdout.split('\n').filter(line => line.trim() !== '');
//
//   // 读取每个文件内容，通过 frontMatter 相关方法找到对应部分，裁掉
//   // 看看剩下的内容里有没有匹配的
//   const results: { name: ThingName, line: ContentLineExact }[] = [];
//   for (const filePath of matchedFiles) {
//     const thingName = getThingNameFromPath(filePath, FileType.FileTypeEntity);
//     const fileLines = readFileContent(libraryName, FileType.FileTypeEntity, thingName);
//     const frontMatter = locateFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: thingName});
//     let contentLines: string[];
//     if (frontMatter) {
//       contentLines = fileLines.slice(0, frontMatter.beginLineNumber - 1)
//         .concat(fileLines.slice(frontMatter.endLineNumber));
//     } else {
//       contentLines = fileLines;
//     }
//     const contentRegex = new RegExp(contentRegexPattern);
//     contentLines.forEach((line, index) => {
//       if (contentRegex.test(line)) {
//         results.push({
//           name: thingName,
//           line: line as ContentLineExact
//         });
//       }
//     });
//   }
//
//   return results;
// }
//
// export function findEntityByFrontMatterRegex(libraryName: LibraryName, fileGlobPattern: string, frontMatterRegexPattern: string): {
//   name: ThingName,
//   line: FrontMatterLine
// }[] {
//
//   // 先 grep 内容
//   const entityDirPath = getEntityDirPath(libraryName);
//   const fullGlobPath = path.join(entityDirPath, fileGlobPattern);
//   const grepResult = shell.grep('-l', frontMatterRegexPattern, fullGlobPath);
//   const matchedFiles = grepResult.stdout.split('\n').filter(line => line.trim() !== '');
//
//   const results: { name: ThingName, line: FrontMatterLine }[] = [];
//   for (const filePath of matchedFiles) {
//     const thingName = getThingNameFromPath(filePath, FileType.FileTypeEntity);
//     const fileLines = readFileContent(filePath, FileType.FileTypeEntity, thingName);
//     const frontMatter = locateFrontMatter({library: libraryName, type: FileType.FileTypeEntity, name: thingName});
//     if (frontMatter) {
//       const frontMatterLines = fileLines.slice(frontMatter.beginLineNumber - 1, frontMatter.endLineNumber);
//       const frontMatterRegex = new RegExp(frontMatterRegexPattern);
//       frontMatterLines.forEach((line) => {
//         if (frontMatterRegex.test(line)) {
//           results.push({
//             name: thingName,
//             line: line as FrontMatterLine
//           });
//         }
//       });
//     }
//   }
//
//   return results;
// }
