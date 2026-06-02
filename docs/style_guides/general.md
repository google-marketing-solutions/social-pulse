# General Code Style Guide

This document outlines the general coding standards that apply to all files
within the Gemini Social Sentiment Analyzer project, regardless of the programming language used.

## 1. Line Length
- **Maximum Line Length:** By default, all lines of code and documentation
  should be limited to a maximum of 80 characters.
- **Exceptions:** This rule applies universally unless it is explicitly
  overwritten by a specific language's style rule (e.g. if a language-specific
  linter strictly requires longer lines for certain imports or generated code).
  However, in the absence of such strictly mandated exceptions, the
  80-character limit must be strictly adhered to.

## 2. Trailing whitespace
- **Trailing whitespace:** No trailing whitespace is allowed in any file.
  This applies to all files, regardless of the programming language used.

## 3. Commit messages
- **Commit message:** All commit messages must be in the form of a imperative
  sentence. For example, instead of "Fixes bug", use "Fix bug".
- **Subject line:** The subject line must be 50 characters or less. It should be
  a concise summary of the changes.  It should also start with a prefix that
  indicates the type of change (e.g. "feat:", "fix:", "docs:", "test:",
  "chore:", "refactor:", "perf:", "style:", "build:", "ci:").
- **Body:** The body should be a more detailed explanation of the changes. It
  should be wrapped at 72 characters.  Each bullet point should start with a
  symbol such as "-" or "*", and limit it to only 3 bullet points max.
- **Separation:** The subject line and the body must be separated by exactly
  one blank line (an empty line).

## 4. Markdown files
- **Markdown files:** All markdown files must be formatted according to the
  Google Markdown Style Guide.
