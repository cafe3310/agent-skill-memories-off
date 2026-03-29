import {afterEach, beforeEach, describe, expect, it, type Mock, spyOn} from 'bun:test';
import '@src/tests/setup';
import * as mockSetup from "@src/tests/setup";
import {
  type ContentLocator,
  type FileContent,
  FileType,
  type LibraryName,
  type ThingLocator,
  type ThingName
} from "@src/entities/editor/types.ts";
import fs from 'fs';
import shell from "shelljs";
import {
  addContentToThing,
  appendInHeading,
  innerReplace,
  replaceContent,
  replaceInHeading,
  replaceSection
} from "./editing.ts";

const MOCK_LIBRARY_NAME: LibraryName = mockSetup.MOCK_LIBRARY_NAME;
const MOCK_ENTITY_NAME: ThingName = mockSetup.MOCK_ENTITY_NAME;
const MOCK_FILE_CONTENT: FileContent = [
  '# Welcome',                      // 1
  '',                               // 2
  'This is the introduction.',      // 3
  'It has two lines.',              // 4
  '',                               // 5
  '## Section 1: Details',          // 6
  '',                               // 7
  'Here is some detail.',           // 8
  'Line to be deleted.',            // 9
  'Another line.',                  // 10
  '',                               // 11
  '## Section 2: More Details',     // 12
  '',                               // 13
  'Final content here.',            // 14
  '## Section 3: Empty',            // 15
  ''                                // 16
];
const MOCK_TARGET: ThingLocator = {
  library: MOCK_LIBRARY_NAME,
  type: FileType.FileTypeEntity,
  name: MOCK_ENTITY_NAME,
};

describe('editing', () => {

  const shellTestSpy: Mock<(...args: unknown[]) => boolean> = spyOn(shell, 'test') as Mock<(...args: unknown[]) => boolean>;
  const readSpy: Mock<(...args: unknown[]) => string> = spyOn(fs, 'readFileSync') as Mock<(...args: unknown[]) => string>;
  const writeSpy: Mock<(...args: unknown[]) => void> = spyOn(fs, 'writeFileSync') as Mock<(...args: unknown[]) => void>;

  beforeEach(() => {
    shellTestSpy.mockClear();
    readSpy.mockClear();
    writeSpy.mockClear();
  });

  describe('innerReplace', () => {
    it('should replace a block of lines', () => {
      const result = innerReplace(MOCK_FILE_CONTENT, 8, 9, ['New line 1', 'New line 2']);
      expect(result).toHaveLength(MOCK_FILE_CONTENT.length);
      expect(result[7]).toBe('New line 1');
      expect(result[8]).toBe('New line 2');
      expect(result.join('\n')).not.toContain('Here is some detail.');
    });

    it('should delete a block of lines when newBlock is empty', () => {
      const result = innerReplace(MOCK_FILE_CONTENT, 8, 9, []);
      expect(result).toHaveLength(MOCK_FILE_CONTENT.length - 2);
      expect(result.join('\n')).not.toContain('Here is some detail.');
      expect(result.join('\n')).not.toContain('Line to be deleted.');
      expect(result[7]).toBe('Another line.');
      expect(result[6]).toBe('');
    });

    it('should insert lines when beginLineNo > endLineNo, pushing beginLineNo afterwards', () => {
      const result = innerReplace(MOCK_FILE_CONTENT, 6, 5, ['Inserted line 1', 'Inserted line 2']);
      expect(result).toHaveLength(MOCK_FILE_CONTENT.length + 2);
      expect(result[5]).toBe('Inserted line 1');
      expect(result[6]).toBe('Inserted line 2');
      expect(result[7]).toBe('## Section 1: Details');
    });

    it('should insert lines at the front of file when beginLineNo = 1 endLineNo are 0', () => {
      const result = innerReplace(MOCK_FILE_CONTENT, 1, 0, ['Intro line 1', 'Intro line 2']);
      expect(result).toHaveLength(MOCK_FILE_CONTENT.length + 2);
      expect(result[0]).toBe('Intro line 1');
      expect(result[1]).toBe('Intro line 2');
      expect(result[2]).toBe('# Welcome');
    });

    it('should append lines at the end of file when beginLineNo = endLineNo = total lines', () => {
      const result = innerReplace(MOCK_FILE_CONTENT, MOCK_FILE_CONTENT.length + 1, MOCK_FILE_CONTENT.length, ['Final line 1', 'Final line 2']);
      expect(result).toHaveLength(MOCK_FILE_CONTENT.length + 2);
      expect(result[result.length - 2]).toBe('Final line 1');
      expect(result[result.length - 1]).toBe('Final line 2');
    });
  });

  describe('replaceContent', () => {
    it('should replace content when a unique locator is provided', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));

      const oldContent: ContentLocator = {
        type: 'Lines',
        contentLines: ['Here is some detail.'],
      };
      const newContent = ['Replaced detail.'];

      replaceContent(MOCK_TARGET, oldContent, newContent);

      expect(writeSpy).toHaveBeenCalledTimes(1);
      const writtenContent = writeSpy.mock.calls[0]![1] as string;
      expect(writtenContent).toEqual(`# Welcome

This is the introduction.
It has two lines.

## Section 1: Details

Replaced detail.
Line to be deleted.
Another line.

## Section 2: More Details

Final content here.
## Section 3: Empty\n`);
    });

    it('should throw an error if content is not unique', () => {
      readSpy.mockReturnValue(['Line', 'Line'].join('\n'));
      const oldContent: ContentLocator = {
        type: 'Lines',
        contentLines: ['Line'],
      };
      expect(() => replaceContent(MOCK_TARGET, oldContent, ['New Line']))
        .toThrow('发现多个匹配的内容块');
    });
  });

  describe('addContentToThing', () => {
    it('should add content to the end of the file', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));

      const contentToAdd = ['// New final line'];
      addContentToThing(MOCK_TARGET, contentToAdd);

      expect(writeSpy).toHaveBeenCalledTimes(1);
      const writtenContent = writeSpy.mock.calls[0]![1] as string;
      expect(writtenContent).toEqual(`# Welcome

This is the introduction.
It has two lines.

## Section 1: Details

Here is some detail.
Line to be deleted.
Another line.

## Section 2: More Details

Final content here.
## Section 3: Empty

// New final line`);
    });
  });

  describe('replaceInHeading', () => {
    it('should replace content within a specific heading section', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));
      const headingLocator = 'Section 1 details';
      const oldContent: ContentLocator = { type: 'Lines', contentLines: ['Here is some detail.'] };
      const newContent = ['Replaced detail in section 1.'];
      replaceInHeading(MOCK_TARGET, headingLocator, oldContent, newContent);

      expect(writeSpy).toHaveBeenCalledTimes(1);
      const writtenContent = writeSpy.mock.calls[0]![1] as string;
      expect(writtenContent).toEqual(`# Welcome

This is the introduction.
It has two lines.

## Section 1: Details

Replaced detail in section 1.
Line to be deleted.
Another line.

## Section 2: More Details

Final content here.
## Section 3: Empty\n`);
    });

    it('should throw if heading is not found', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));
      const headingLocator = 'Section 1: Nonexistent';
      const oldContent: ContentLocator = { type: 'Lines', contentLines: ['...'] };
      expect(() => replaceInHeading(MOCK_TARGET, headingLocator, oldContent, []))
        .toThrow('匹配的章节');
    });

    it('should throw if content is not found within the heading', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));
      const headingLocator = 'Section 1: Details';
      const oldContent: ContentLocator = { type: 'Lines', contentLines: ['Final content here.'] }; // This content is in Section 2
      expect(() => replaceInHeading(MOCK_TARGET, headingLocator, oldContent, []))
        .toThrow('匹配的内容块');
    });
  });

  describe('appendInHeading', () => {
    it('should append content to the end of a specific heading section', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));
      const headingLocator = 'Section 2 more details';
      const newContent = ['Appended line in section 2.'];
      appendInHeading(MOCK_TARGET, headingLocator, newContent);

      expect(writeSpy).toHaveBeenCalledTimes(1);
      const writtenContent = writeSpy.mock.calls[0]![1] as string;
      expect(writtenContent).toEqual(`# Welcome

This is the introduction.
It has two lines.

## Section 1: Details

Here is some detail.
Line to be deleted.
Another line.

## Section 2: More Details

Final content here.
Appended line in section 2.
## Section 3: Empty\n`);
    });
  });

  describe('replaceSection', () => {
    it('should replace the entire content of a section', () => {
      readSpy.mockReturnValue(MOCK_FILE_CONTENT.join('\n'));
      const headingLocator = 'Section 1 details';
      const newContent = ['This is the new section 1.'];
      replaceSection(MOCK_TARGET, headingLocator, newContent);

      expect(writeSpy).toHaveBeenCalledTimes(1);
      const writtenContent = writeSpy.mock.calls[0]![1] as string;
      expect(writtenContent).toEqual(`# Welcome

This is the introduction.
It has two lines.

## Section 1: Details
This is the new section 1.
## Section 2: More Details

Final content here.
## Section 3: Empty\n`);
    });
  });

  const MOCK_CONTENT_WITH_YAML: FileContent = [
    '---',
    'key: value',
    '---',
    '# Welcome',
    '',
    '## Section 1',
    'Content of section 1.',
    '',
    '## Section 2',
    'Content of section 2.',
  ];

  const MOCK_CONTENT_YAML_AND_PRE_CONTENT: FileContent = [
    '---',
    'key: value',
    '---',
    'Some content before any heading.',
    '',
    '## Section 1',
    'Content of section 1.',
  ];

  const MOCK_CONTENT_YAML_NO_HEADINGS: FileContent = [
    '---',
    'key: value',
    '---',
    'Just a single block of content.',
    'No headings in this file.',
  ];

  describe('with complex layouts', () => {
    describe('with YAML front matter', () => {
      it('should correctly replace a section', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_WITH_YAML.join('\n'));
        replaceSection(MOCK_TARGET, 'Section 1', ['New content for section 1.']);
        expect(writeSpy).toHaveBeenCalledTimes(1);
        const writtenContent = writeSpy.mock.calls[0]![1] as string;
        expect(writtenContent).toEqual(`---
key: value
---
# Welcome

## Section 1
New content for section 1.
## Section 2
Content of section 2.`);
      });

      it('should correctly append to a section', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_WITH_YAML.join('\n'));
        appendInHeading(MOCK_TARGET, 'Section 2', ['Appended content.']);
        expect(writeSpy).toHaveBeenCalledTimes(1);
        const writtenContent = writeSpy.mock.calls[0]![1] as string;
        expect(writtenContent).toEqual(`---
key: value
---
# Welcome

## Section 1
Content of section 1.

## Section 2
Content of section 2.
Appended content.`);
      });
    });

    describe('with YAML and pre-heading content', () => {
      it('should correctly replace a section after pre-heading content', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_YAML_AND_PRE_CONTENT.join('\n'));
        replaceSection(MOCK_TARGET, 'Section 1', ['New content for section 1.']);
        expect(writeSpy).toHaveBeenCalledTimes(1);
        const writtenContent = writeSpy.mock.calls[0]![1] as string;
        expect(writtenContent).toEqual(`---
key: value
---
Some content before any heading.

## Section 1
New content for section 1.`);
      });

      it('should be able to replace the pre-heading content using replaceContent', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_YAML_AND_PRE_CONTENT.join('\n'));
        const oldContent: ContentLocator = { type: 'Lines', contentLines: ['Some content before any heading.'] };
        replaceContent(MOCK_TARGET, oldContent, ['Replaced pre-heading content.']);
        expect(writeSpy).toHaveBeenCalledTimes(1);
        const writtenContent = writeSpy.mock.calls[0]![1] as string;
        expect(writtenContent).toEqual(`---
key: value
---
Replaced pre-heading content.

## Section 1
Content of section 1.`);
      });
    });

    describe('with YAML and no headings', () => {
      it('should throw error when trying to use heading-based functions', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_YAML_NO_HEADINGS.join('\n'));
        expect(() => replaceSection(MOCK_TARGET, 'Any Section', ['...'])).toThrow('匹配的章节标题');
        expect(() => appendInHeading(MOCK_TARGET, 'Any Section', ['...'])).toThrow('匹配的章节标题');
      });

      it('should still be able to add content to the end', () => {
        readSpy.mockReturnValue(MOCK_CONTENT_YAML_NO_HEADINGS.join('\n'));
        addContentToThing(MOCK_TARGET, ['Appended content.']);
        expect(writeSpy).toHaveBeenCalledTimes(1);
        const writtenContent = writeSpy.mock.calls[0]![1] as string;
        expect(writtenContent).toEqual(`---
key: value
---
Just a single block of content.
No headings in this file.
Appended content.`);
      });
    });
  });
});
