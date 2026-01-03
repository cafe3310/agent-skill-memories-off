import {describe, expect, it} from 'bun:test';
import '@src/tests/setup';

import {normalizeHeading, normalizeReason, toHeadingLine, normalizeYamlKey, normalizeFrontMatterLine} from "./text.ts";

describe('', () => {
  it('normalize', () => {
    expect(normalizeHeading('  ## Section 1: Details,  ')).toBe('section 1 details');
    expect(normalizeHeading('Another Example (with parens!)')).toBe('another example with parens');
    expect(normalizeHeading('  Multiple   Spaces  ')).toBe('multiple spaces');
    expect(normalizeHeading('A Title\nWith Newlines')).toBe('a title with newlines');
  });

  it('normalizeReason', () => {
    expect(normalizeReason('  This is a reason! It explains why.  ')).toBe('This is a reason It explains why');
    expect(normalizeReason(undefined)).toBe('');
  });

  it('toTocLine', () => {
    expect(toHeadingLine('My Section')).toBe('## my section');
    expect(toHeadingLine(' Another Section: Details ', 3)).toBe('### another section details');
  });

  it('normalizeYamlKey', () => {
    // Basic normalization
    expect(normalizeYamlKey('  Key With   Spaces  ')).toBe('key with spaces');
    expect(normalizeYamlKey('Another_Key-Test')).toBe('another_keytest');
    expect(normalizeYamlKey('Key with New\nLine')).toBe('key with new line');
    expect(normalizeYamlKey('KEY')).toBe('key');
    expect(normalizeYamlKey('')).toBe('');

    // Removal of YAML special characters
    expect(normalizeYamlKey('key:value')).toBe('keyvalue');
    expect(normalizeYamlKey('- list item')).toBe('list item');
    expect(normalizeYamlKey('? query')).toBe('query');
    expect(normalizeYamlKey('[array]')).toBe('array');
    expect(normalizeYamlKey('{object}')).toBe('object');
    expect(normalizeYamlKey('# comment')).toBe('comment');
    expect(normalizeYamlKey('& anchor')).toBe('anchor');
    expect(normalizeYamlKey('* alias')).toBe('alias');
    expect(normalizeYamlKey('!tag')).toBe('tag');
    expect(normalizeYamlKey('| block')).toBe('block');
    expect(normalizeYamlKey('> fold')).toBe('fold');
    expect(normalizeYamlKey('"quoted"')).toBe('quoted');
    expect(normalizeYamlKey('%directive')).toBe('directive');
    expect(normalizeYamlKey('@handle')).toBe('handle');
    expect(normalizeYamlKey('`literal`')).toBe('literal');
    expect(normalizeYamlKey('key,with,comma')).toBe('keywithcomma');
    expect(normalizeYamlKey('key.with.dot')).toBe('key.with.dot'); // Dot is not removed by default
    expect(normalizeYamlKey('Key: value & another')).toBe('key value another');
  });

  it('normalizeFrontMatterLine', () => {
    // Line with key-value pair
    expect(normalizeFrontMatterLine('  title: My Document  ')).toBe('title: My Document');
    expect(normalizeFrontMatterLine('Key With Spaces: value')).toBe('key with spaces: value');
    expect(normalizeFrontMatterLine('key: value with: colon')).toBe('key: value with: colon'); // Only first colon splits
    expect(normalizeFrontMatterLine('  nested: {a: 1}  ')).toBe('nested: {a: 1}');
    expect(normalizeFrontMatterLine('yaml: key with : value')).toBe('yaml: key with : value');
    expect(normalizeFrontMatterLine('key-with-!: value')).toBe('keywith: value');

    // Line without colon (entire line as key)
    expect(normalizeFrontMatterLine('  just a key  ')).toBe('just a key');
    expect(normalizeFrontMatterLine('another key & value')).toBe('another key value');

    // Empty line
    expect(normalizeFrontMatterLine('')).toBe('');
    expect(normalizeFrontMatterLine('  ')).toBe('');
  });
});
