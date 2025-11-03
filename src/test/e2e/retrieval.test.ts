import { afterAll, beforeAll, describe, expect, test } from 'bun:test';
import type { ChildProcess } from 'node:child_process';
import {
  killMcp,
  resetLibAndBootMcp,
  callMcp,
} from './util.test';

describe('E2E Retrieval Tools', () => {
  let serverProcess: ChildProcess;

  beforeAll(() => {
    serverProcess = resetLibAndBootMcp();
  });

  afterAll(() => {
    killMcp(serverProcess);
  });

  test('should find entities by content and display TOC using searchInContents tool', async () => {
    // 1. Create an entity with specific content and multi-level headings
    const entity = {
      name: 'search-toc-entity',
      content: '# Heading 1\nThis is some content.\n## Subheading 1.1\nHere is a unique phrase for testing: "apple banana cherry".\nMore text here.'
    };
    await callMcp(serverProcess, 'tools/call', {
      name: 'addEntities',
      arguments: { libraryName: 'test-library', entity: entity },
    });

    // 2. Search for content that exists under a subheading
    const responseExists = await callMcp(serverProcess, 'tools/call', {
      name: 'searchInContents',
      arguments: { libraryName: 'test-library', contentGlob: '*unique phrase*' },
    });

    // 3. Verify the entity and TOC are found and correctly formatted
    expect(responseExists).toContain('===search-toc-entity===');
    expect(responseExists).toContain('## Subheading 1.1');
    expect(responseExists).toContain('Here is a unique phrase for testing: "apple banana cherry".');
    expect(responseExists).toContain('===search-toc-entity MATCHES END===');

    // 4. Search for content that does not exist
    const responseNotExists = await callMcp(serverProcess, 'tools/call', {
      name: 'searchInContents',
      arguments: { libraryName: 'test-library', contentGlob: '*nonexistent-phrase*' },
    });

    // 5. Verify the entity is not found
    expect(responseNotExists).not.toContain('===search-toc-entity===');
  }, 10000);

  test('should find entities by metadata and display matched key-value pairs', async () => {
    // 1. Create an entity with specific metadata
    const entity = {
      name: 'metadata-test-entity',
      content: '---\nentity type: Test\naliases: test-alias\n---\nThis is a test entity for metadata search.'
    };
    await callMcp(serverProcess, 'tools/call', {
      name: 'addEntities',
      arguments: { libraryName: 'test-library', entity: entity },
    });

    // 2. Search for metadata that exists
    const responseExists = await callMcp(serverProcess, 'tools/call', {
      name: 'findEntitiesByMetadata',
      arguments: { libraryName: 'test-library', metadataQuery: { 'entity type': 'Test' } },
    });

    // 3. Verify the entity and matched key-value pair are found and correctly formatted
    expect(responseExists).toContain('- metadata-test-entity (entity type: Test)');

    // 4. Search for metadata that does not exist
    const responseNotExists = await callMcp(serverProcess, 'tools/call', {
      name: 'findEntitiesByMetadata',
      arguments: { libraryName: 'test-library', metadataQuery: { 'entity type': 'NonExistent' } },
    });

    // 5. Verify the entity is not found
    expect(responseNotExists).not.toContain('- metadata-test-entity');
  }, 10000);
});
