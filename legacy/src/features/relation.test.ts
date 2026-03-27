import {afterAll, beforeAll, describe, expect, test} from 'bun:test';
import type {ChildProcess} from 'node:child_process';

import path from 'path';
import fs from 'fs';
import {callMcp, expectFileTotalLines, killMcp, resetLibAndBootMcp, tempLibraryPath} from "@src/tests/e2e/util.test.ts";

describe('E2E Relation Tools Lifecycle', () => {
  let serverProcess: ChildProcess;
  const libraryName = 'test-library';
  const entity1Name = 'entity-with-relations';
  const entity2Name = 'related-entity-1';
  const entity3Name = 'related-entity-2';
  const entity1Path = path.join(tempLibraryPath, 'entities', `${entity1Name}.md`);
  const entity2Path = path.join(tempLibraryPath, 'entities', `${entity2Name}.md`);
  const entity3Path = path.join(tempLibraryPath, 'entities', `${entity3Name}.md`);

  beforeAll(() => {
    serverProcess = resetLibAndBootMcp();
    // Create some initial entities for testing relations
    fs.writeFileSync(entity1Path, `---
entity type: test
---
# ${entity1Name}
Content for entity 1.`);
    fs.writeFileSync(entity2Path, `---
entity type: test
---
# ${entity2Name}
Content for entity 2.`);
    fs.writeFileSync(entity3Path, `---
entity type: test
---
# ${entity3Name}
Content for entity 3.`);
  });

  afterAll(() => {
    killMcp(serverProcess);
  });

  test('should create and delete relations using correct schema', async () => {
    // Step 1: Create relations
    let response = await callMcp(serverProcess, 'tools/call', {
      name: 'createRelations',
      arguments: {
        libraryName: libraryName,
        relations: [
          `${entity1Name}, knows, ${entity2Name}`,
          `${entity1Name}, likes, ${entity3Name}`,
        ],
        reason: "Initial relation creation test"
      },
    });

    expect(response).toContain('CREATED RELATIONS');
    expect(response).toContain(`- ${entity1Name}, knows, ${entity2Name}`);
    expect(response).toContain(`- ${entity1Name}, likes, ${entity3Name}`);

    expectFileTotalLines(entity1Path, [
      '---',
      'entity type: test',
      'relation as knows: related-entity-1',
      'relation as likes: related-entity-2',
      '---',
      `# ${entity1Name}`,
      'Content for entity 1.',
    ]);

    // Step 2: Attempt to create existing relation (should not duplicate)
    response = await callMcp(serverProcess, 'tools/call', {
      name: 'createRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${entity1Name}, knows, ${entity2Name}`],
        reason: "Attempt to create duplicate relation"
      },
    });
    expect(response).toContain('NO ACTION TAKEN');

    // File should remain unchanged
    expectFileTotalLines(entity1Path, [
      '---',
      'entity type: test',
      'relation as knows: related-entity-1',
      'relation as likes: related-entity-2',
      '---',
      `# ${entity1Name}`,
      'Content for entity 1.',
    ]);

    // Step 3: Delete one relation
    response = await callMcp(serverProcess, 'tools/call', {
      name: 'deleteRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${entity1Name}, knows, ${entity2Name}`],
        reason: "Delete one relation"
      },
    });

    expect(response).toContain('DELETED RELATIONS');
    expect(response).toContain(`- ${entity1Name}, knows, ${entity2Name}`);

    expectFileTotalLines(entity1Path, [
      '---',
      'entity type: test',
      'relation as likes: related-entity-2',
      '---',
      `# ${entity1Name}`,
      'Content for entity 1.',
    ]);

    // Step 4: Delete the remaining relation
    response = await callMcp(serverProcess, 'tools/call', {
      name: 'deleteRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${entity1Name}, likes, ${entity3Name}`],
        reason: "Delete remaining relation"
      },
    });

    expect(response).toContain('DELETED RELATIONS');
    expect(response).toContain(`- ${entity1Name}, likes, ${entity3Name}`);

    expectFileTotalLines(entity1Path, [
      '---',
      'entity type: test',
      '---',
      `# ${entity1Name}`,
      'Content for entity 1.',
    ]);
  }, 10000);

  test('should handle failure and edge scenarios for createRelations', async () => {
    // Scenario 1: Source entity does not exist
    const nonExistentSource = 'non-existent-source';
    let response = await callMcp(serverProcess, 'tools/call', {
      name: 'createRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${nonExistentSource}, knows, ${entity2Name}`],
        reason: "Test with non-existent source"
      },
    });

    expect(response).toContain('FAILED RELATIONS');
    expect(response).toContain(`- ${nonExistentSource}, knows, ${entity2Name}: 无法找到文件`);

    // Scenario 2: Target entity does not exist (should succeed as per documentation)
    const nonExistentTarget = 'non-existent-target';
    response = await callMcp(serverProcess, 'tools/call', {
      name: 'createRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${entity1Name}, follows, ${nonExistentTarget}`],
        reason: "Test with non-existent target"
      },
    });

    expect(response).toContain('CREATED RELATIONS');
    expect(response).toContain(`- ${entity1Name}, follows, ${nonExistentTarget}`);
    const entity1Content = fs.readFileSync(entity1Path, 'utf-8');
    expect(entity1Content).toContain(`relation as follows: ${nonExistentTarget}`);
  }, 10000);

  test('should handle no-op scenarios for deleteRelations', async () => {
    // Scenario 1: Try to delete a relation that doesn't exist
    const response = await callMcp(serverProcess, 'tools/call', {
      name: 'deleteRelations',
      arguments: {
        libraryName: libraryName,
        relations: [`${entity1Name}, dislikes, ${entity2Name}`], // This relation does not exist
        reason: "Test deleting non-existent relation"
      },
    });

    expect(response).toContain('NO ACTION TAKEN');
  }, 10000);
});
