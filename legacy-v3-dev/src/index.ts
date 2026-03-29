import {runV2} from "@src/v2.ts";

console.error('Booting v2 server...');

runV2().then(() => {
  console.error('v2 server is running.');
}).catch(error => {
  console.error('Failed to run v2 server:', error);
  process.exit(1);
});
