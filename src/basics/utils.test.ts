import {describe, expect, it, beforeEach, afterEach} from 'bun:test';
import '@src/tests/setup';
import {checks, checkObjHas, getEnvVar, globToRegex} from './utils';

describe('utils', () => {
  // Tests for checks
  describe('checks', () => {
    it('should not throw an error if the condition is true', () => {
      expect(() => checks(true, 'This should not throw')).not.toThrow();
    });

    it('should throw an error if the condition is false', () => {
      expect(() => checks(false, 'This is an error message')).toThrow('This is an error message');
    });
  });

  // Tests for checkObjHas
  describe('checkObjHas', () => {
    const testObj = {name: 'Gemini', version: 1.0};

    it('should not throw an error for a valid object, key, and type', () => {
      expect(() => checkObjHas(testObj, 'name', 'string')).not.toThrow();
      expect(() => checkObjHas(testObj, 'version', 'number')).not.toThrow();
    });

    it('should throw an error if the object is not a valid object', () => {
      expect(() => checkObjHas(null, 'key', 'string')).toThrow('Type check failed: key is not string');
      expect(() => checkObjHas(undefined, 'key', 'string')).toThrow('Type check failed: key is not string');
      expect(() => checkObjHas('a string', 'key', 'string')).toThrow('Type check failed: key is not string');
    });

    it('should throw an error if the key is missing', () => {
      expect(() => checkObjHas(testObj, 'missingKey', 'string')).toThrow('Type check failed: missingKey is not string');
    });

    it('should throw an error if the key has the wrong type', () => {
      expect(() => checkObjHas(testObj, 'name', 'number')).toThrow('Type check failed: name is not number');
    });
  });

  // Tests for getEnvVar
  describe('getEnvVar', () => {
    const ORIGINAL_ENV = process.env;

    beforeEach(() => {
      // Bun has a bug where `process.env` becomes read-only, so we reset it this way
      process.env = { ...ORIGINAL_ENV };
    });

    afterEach(() => {
      process.env = ORIGINAL_ENV;
    });

    it('should return the environment variable if it is set', () => {
      process.env['TEST_VAR'] = 'test_value';
      expect(getEnvVar('TEST_VAR', 'default')).toBe('test_value');
    });

    it('should return the default value if the environment variable is not set', () => {
      delete process.env['TEST_VAR'];
      expect(getEnvVar('TEST_VAR', 'default_value')).toBe('default_value');
    });
  });

  // Tests for globToRegex
  describe('globToRegex', () => {
    it('should convert * to .*', () => {
      expect(globToRegex('*.ts')).toBe('.*\\.ts');
    });

    it('should convert ? to .', () => {
      expect(globToRegex('file?.log')).toBe('file.\\.log');
    });

    it('should escape special regex characters', () => {
      expect(globToRegex('file(1).log+')).toBe('file\\(1\\)\\.log\\+');
    });

    it('should handle a combination of wildcards and special characters', () => {
      expect(globToRegex('path/to/*(v?).ts')).toBe('path/to/.*\\(v.\\)\\.ts');
    });
  });
});
