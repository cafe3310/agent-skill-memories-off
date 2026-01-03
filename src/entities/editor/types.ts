import type {WeakOpaque} from "@src/basics/types.ts";

// region 命名和路径

// 文件类型
export const enum FileType {
  FileTypeEntity,
  FileTypeJourney,
  FileTypeMeta,
}

// 事物名称 - 如实体名称，记录名称。不带文件后缀名
export type ThingName = WeakOpaque<string, 'ThingName'>;

// 知识库名称
// 如 "MyProjectDocs" -- 一个名为 MyProjectDocs 的知识库
export type LibraryName = WeakOpaque<string, 'LibraryName'>;

// 文件相对路径，相对于知识库根目录。
// 如 "guides/installation.md" -- 知识库根目录下的 guides 文件夹中的 installation.md 文件
export type FileRelativePath = WeakOpaque<string, 'FileRelativePath'>;

// 文件绝对路径
// 如 "/home/user/docs/MyProjectDocs/guides/installation.md"
export type FileAbsolutePath = WeakOpaque<string, 'FileAbsolutePath'>;

// 文件夹绝对路径
// 如 "/home/user/docs/MyProjectDocs/entities"
export type FolderAbsolutePath = WeakOpaque<string, 'FolderAbsolutePath'>;

// 在仓库中定位某个文件的结构化描述
export type ThingLocator = {
  library: LibraryName;
  type: FileType;
  name: ThingName;
}

// endregion

// region content
// 我们对内容的定义是
// content 包括 toc, frontmatter, 以及普通正文

// 模糊匹配的内容块，基于行。
// 如 "this is the beginning of the section*" -- 表达「可匹配任何对应内容的块」的 filter
export type ContentLineGlob = WeakOpaque<string, 'ContentLinesGlob'>;

// 精确匹配的内容块，单行。
// 如 "  - This is the beginning of the section." -- 表达「只能匹配对应内容的块」的 filter
export type ContentLineExact = WeakOpaque<string, 'ContentLinesExact'>;

// 行号，从 1 开始计数
export type ContentLineNumber = WeakOpaque<number, 'ContentLineNumber'>;

// 用于定位文件中某个位置的内容上下文块。
// 可以是基于行号的范围，或者是基于内容的精确块。
export type ContentLocator = {
  type: 'NumbersAndLines'
  beginLineNumber: ContentLineNumber;
  endLineNumber: ContentLineNumber;
  beginContentLine: ContentLineExact;
  endContentLine: ContentLineExact;
} | {
  type: 'Lines'
  contentLines: ContentLineExact[];
}

// 已解析的内容定位器，包含目标事物定位器和内容定位器的详细信息
export type ResolvedContentLocator = {
  target: ThingLocator,
  origin: ContentLocator | 'frontmatter',
  beginLineNumber: ContentLineNumber;
  endLineNumber: ContentLineNumber;
  beginContentLine: ContentLineExact;
  endContentLine: ContentLineExact;
}

// 整个文件的所有行
export type FileContent = WeakOpaque<string[], 'FileContent'>;

// endregion

// region Heading 和 Toc

// 模糊匹配的章节标题。
// 如 "installation guide"
export type HeadingGlob = WeakOpaque<string, 'HeadingGlob'>;

// 精确匹配的章节标题行。
// 如 "## Installation (Guide):"
export type HeadingExact = WeakOpaque<string, 'HeadingExact'>;

// 标题层级，从 1 开始计数
// 1 - #
// 2 - ##
// ...
// 6 - ######
export type HeadingLevel = WeakOpaque<number, 'HeadingLevel'>;

// 一个 Toc 行在文件中的结构化描述
export type Heading = {
  level: HeadingLevel;
  lineNumber: ContentLineNumber;
  text: HeadingExact;
}

// 一个文件的所有目录行列表
// TocList, Array of {level, lineNumber, text}
// 如 [
//   { level: 1, lineNumber: 3, text: "# Installation" },
//   { level: 2, lineNumber: 10, text: "## Step 1" },
//   ...
// ]
export type Toc = Heading[];

// endregion
// region Front Matter
// 我们定义 frontmatter 只能是一级键值对，键和值均为字符串 - 而且每个项目必须仅占一行。
// frontmatter 中的不同类型 key 可以通过前缀区分，例如 "relation xxx: content", "relation yyy: content"

export type FrontMatterLine = WeakOpaque<string, 'FrontMatterLine'>;

// 一个 frontmatter 项目的结构化描述
export type FrontMatterEntry = {name: string, value: string};

// 整个 frontmatter 的结构化描述
export type FrontMatter = FrontMatterEntry[];

// 预定义的 frontmatter key 列表
export const enum FrontMatterPresetKeys {
  // 例子：'entity type: Person'
  EntityType = 'entity type',
  // 例子：'date modified: 2024-01-01'
  DateModified = 'date modified',
  // 例子：'date created: 2023-12-31'
  DateCreated = 'date created',
  // 例子：'relation as member: team_name'
  RelationAs = 'relation as',
  // 例子：'aliases: alias1, alias2'
  Aliases = 'aliases',
}

// endregion
