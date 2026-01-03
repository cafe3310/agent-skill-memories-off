import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import {ENV_VARS, getEnvVar, logfile, setLogOutputFile} from "@src/basics/utils.ts";
import {manualTools} from "@src/features/manual.ts";
import {entityTools} from "@src/features/entity.ts";
import {backupTools} from "@src/features/backup.ts";
import {relationTools} from "@src/features/relation.ts";
import {retrievalTools} from "@src/features/retrieval.ts";

// This is the entry point for the v2 server.
export async function runV2() {
  const config = {
    MEM_NAME: getEnvVar(ENV_VARS.MEM_NAME.key, ENV_VARS.MEM_NAME.default),
    MEM_LOG_DIR: getEnvVar(ENV_VARS.MEM_LOG_DIR.key, ENV_VARS.MEM_LOG_DIR.default),
  }
  setLogOutputFile(config.MEM_LOG_DIR);
  logfile('v2', 'Starting MCP server v2...');

  const server = new Server({
    name: config.MEM_NAME,
    version: "2.0.0",
  }, {
    capabilities: {
      tools: {},
    },
  });

  // Register tools
  const allTools = [...manualTools, ...entityTools, ...backupTools, ...relationTools, ...retrievalTools];

  // Register request handlers
  const toolTypes = Object.values(allTools).map(t => t.toolType);
  const toolMap = allTools.map((item) => {
    return { [item.toolType.name]: item };
  }).reduce((acc, curr) => {
    return { ...acc, ...curr };
  });

  server.setRequestHandler(ListToolsRequestSchema, () => ({
    tools: toolTypes,
  }));

  logfile('v2', `Registered tools: ${toolTypes.map(t => t.name).join(', ')}`);

  // Handler for CallTool requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    logfile('v2', `Received request: ${JSON.stringify(request)}`);
    const { name: name, arguments: args } = request.params;
    const tool = toolMap[name];
    if (tool?.handler) {
      try {
        logfile(`v2`, `Invoking tool`, name, `with args:`, args);
        const s = tool.handler(args, name);
        logfile(`v2`, `Invoked Tool`, name, `returned:`, typeof s, `content: `, s);
        return buildMcpResponseWith(s);
      } catch (e) {
        throw new Error(`tools error: ${e}`);
      }
    }
    throw new Error(`Unknown tool: ${name}`);
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  logfile('v2', 'Server v2 started, waiting for connections...');
}

function buildMcpResponseWith(s: string) {
  return {
    content: [ {
      type: 'text',
      text: s }
    ]
  }
}
