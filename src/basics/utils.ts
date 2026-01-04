import fs from "fs";

let disableLogOnError = false;

// 条件断言
// 不满足则抛异常并记录日志
export function checks(condition: boolean, message: string): asserts condition {
  if (!condition) {
    const err = new Error(message);
    if (!disableLogOnError) {
      logfileE('Checks failed', err);
    }
    throw err;
  }
}

// 对象属性和类型断言
// 不满足则抛异常并记录日志
export function checkObjHas<T>(obj: unknown, key: string, valueType: string): asserts obj is T {
  if (
    typeof obj !== "object" ||
    obj === null ||
    !(key in obj) ||
    typeof (obj as Record<string, unknown>)[key] !== valueType
  ) {
    const err = new Error(`Type check failed: ${key} is not ${valueType}`);
    if (!disableLogOnError) {
      logfileE('checkObjHas', err);
    }
    throw err;
  }
}

let logConsole: Console = console;

// 记录到日志 -- 调试
export function logfileV(componentName: string, ...args: unknown[]) {
  logConsole.debug(componentName, ...args);
}

// 记录到日志 -- 信息
export function logfile(componentName: string, ...args: unknown[]) {
  logConsole.info(componentName, ...args);
}

// 记录到日志 -- 警告
export function logfileW(componentName: string, ...args: unknown[]) {
  logConsole.warn(componentName, ...args);
}

// 记录到日志 -- 错误
export function logfileE(componentName: string, error: unknown, ...args: unknown[]) {
  logConsole.error(componentName, error, ...args);
}

// 设置日志输出目录。
// 日志文件会记录在目录中，文件名：mcp-server-memories-off-log-YYYY-MM-DD.log
export function setLogOutputFile(dir: string) {
  const date = new Date().toISOString().split("T")[0];
  const file = `${dir}/mcp-server-memories-off-log-${date}.log`;
  console.error('mcp-server-memories-off log file is at', file);
  logConsole = new console.Console(fs.createWriteStream(file, { flags: 'a' }));
}

// 禁用异常时的日志输出，用于测试环境
export function disableLogError() {
  disableLogOnError = true;
}

export const ENV_VARS = {
  MEM_NAME: {
    key: 'MEM_NAME',
    default: 'memory',
  },
  MEM_LOG_DIR: {
    key: 'MEM_LOG_DIR',
    default: '.',
  },
  MEM_LIBRARIES: {
    key: 'MEM_LIBRARIES',
    default: './memory-library',
  },
}

// 获取环境变量，未设置则返回默认值并记录
export function getEnvVar(key: string, defaultVal: string): string {
  const val = process.env[key];
  if (val === undefined) {
    logfileW('utils', `Env ${key} not set, using default: ${defaultVal}`);
    return defaultVal;
  }
  logfile('utils', `Env ${key}: ${val}`);
  return val;
}

// 将 glob 模式转换为正则表达式字符串
// 输出的正则表达式字符串不包含起始和结束标志（^ 和 $），也不会在前后自动添加 .*
// 例如 "this*is" -> "this.*is"
export function globToRegex(globPattern: string): string {
  // Escape special regex characters
  let regex = globPattern.replace(/[.+^${}()|[\\]/g, '\\$&');
  // Replace glob wildcards with regex equivalents
  regex = regex.replace(/\*/g, '.*'); // * matches any sequence of characters
  regex = regex.replace(/\?/g, '.');  // ? matches any single character
  return regex;
}

export function deepFreeze<T>(object: T): T {
  // Retrieve the property names defined on object
  const propNames = Object.getOwnPropertyNames(object);

  // Freeze the properties before freezing the object itself
  for (const name of propNames) {
    // @ts-expect-error 绕过类型检查
    const value = object[name] as unknown;

    // Recurse if the value is an object or array
    if (value && typeof value === "object" && !Object.isFrozen(value)) {
      deepFreeze(value);
    }
  }
  return Object.freeze(object);
}
