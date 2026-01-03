import type {FrontMatterLine} from "@src/entities/editor/types.ts";

// 标准化 Heading 以方便进行 Heading 匹配。
// 标准化包括：去掉首尾空白、多余空白、标点符号，小写化
// e.g. "  ##  Hello, World!  " -> "hello world"
export function normalizeHeading(heading: string): string {
  // 1. 多个空白归一化为单个空格
  heading = heading.replace(/\s+/g, ' ');

  // 2. 移除所有标点符号（中文和英文）
  heading = heading.replace(/[.,\\/#!$%^&*;:{}=\-_`~()，。、《》？；：‘’“”【】（）…]/g, '');

  // 移除换行符
  heading = heading.replace(/[\r\n]/g, '');

  // 3. 小写化
  heading = heading.toLowerCase();

  // 4. 去掉首尾空白
  return heading.trim();
}

// 标准化「调用理由」文本，给 LLM 一个简洁的描述。
// 限制长度到 80, 去掉首尾空白/连续空白/符号
// e.g. "  This is a sample reason, with punctuation!  " -> "This is a sample reason with punctuation"
export function normalizeReason(reason?: string): string {

  if (!reason) {
    return '';
  }

  // 1. 多个空白归一化为单个空格
  reason = reason.replace(/\s+/g, ' ');

  // 2. 移除所有符号（中文和英文）
  reason = reason.replace(/[.,\\/#!$%^&*;:{}=\-_`~()，。、《》？；：‘’“”【】（）…]/g, '');

  // 3. 移除换行符
  reason = reason.replace(/[\r\n]/g, '');

  // 4. trim
  reason = reason.trim();

  // 5. 限制长度到 80, 超过补 '…'
  if (reason.length > 80) {
    reason = reason.slice(0, 78) + '…';
  }

  return reason;
}

// 标准化 YAML Key：去掉首尾空白、多余空白、标点符号，让结果可以被安全地用作 Frontmatter 的 Key。
// e.g. "  my-key: " -> "mykey"
export function normalizeYamlKey(yamlKey: string): string {
  // 1. 替换掉所有 yaml 关键字符号
  yamlKey = yamlKey.replace(/[:\-?[\]{}#,&*!|>'"%@`]/g, '');

  // 2. 多个空白归一化为单个空格
  yamlKey = yamlKey.replace(/\s+/g, ' ');

  // 3. 移除换行符
  yamlKey = yamlKey.replace(/[\r\n]/g, '');

  // 4. 小写化
  yamlKey = yamlKey.toLowerCase();

  // 5. 去掉首尾空白
  return yamlKey.trim();
}

// 标准化 Frontmatter 行：对键进行 normalizeYamlAttr，值保持不变
// e.g. "  My-Key: Some Value  " -> "mykey: Some Value"
export function normalizeFrontmatterLine(frontmatterLine: FrontMatterLine): FrontMatterLine {
  // 从第一个 ':' 处分割键值对，然后分别 normalize 键和值
  // 如果没有 ':'，则整个行作为键，值为空字符串
  const index = frontmatterLine.indexOf(':');
  if (index === -1) {
    return normalizeYamlKey(frontmatterLine);
  } else {
    const key = frontmatterLine.slice(0, index).trim();
    const value = frontmatterLine.slice(index + 1).trim();
    return `${normalizeYamlKey(key)}: ${value}`;
  }
}

// 将任何文本转换成 Heading：先标准化，再加上 #（默认 2 级）
// e.g. "text to heading" -> "## text to heading"
export function textToHeading(text: string, level = 2): string {
  const normalized = normalizeHeading(text);
  const hashes = '#'.repeat(level);
  return `${hashes} ${normalized}`;
}
