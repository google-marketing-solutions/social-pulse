# Google Python Style Guide Summary

This document summarizes key rules and best practices from the Google Python
Style Guide.

## 1. Python Language Rules
- **Linting:** Run `pylint` on your code to catch bugs and style issues.
- **Imports:** Use `import x` for packages/modules. Use `from x import y` only
  when `y` is a submodule.
- **Exceptions:** Use built-in exception classes. Do not use bare `except:`
  clauses.
- **Global State:** Avoid mutable global state. Module-level constants are okay
  and should be `ALL_CAPS_WITH_UNDERSCORES`.
- **Comprehensions:** Use for simple cases. Avoid for complex logic where a
  full loop is more readable.
- **Default Argument Values:** Do not use mutable objects (like `[]` or `{}`)
  as default values.
- **True/False Evaluations:** Use implicit false (e.g., `if not my_list:`).
  Use `if foo is None:` to check for `None`.
- **Type Annotations:** Strongly encouraged for all public APIs.

## 2. Python Style Rules
- **Line Length:** Maximum 80 characters.
- **Indentation:** 2 spaces per indentation level. Never use tabs.
- **Blank Lines:** Two blank lines between top-level definitions (classes,
  functions). One blank line between method definitions.
- **Whitespace:** Avoid extraneous whitespace. Surround binary operators
  with single spaces.
- **Docstrings:** Use `"""triple double quotes"""`. Every public module,
  function, class, and method must have a docstring.
- **Format:** Start with a one-line summary. Include `Args:`, `Returns:`,
  and `Raises:` sections.
- **Strings:** Use f-strings for formatting. Use only double (`"`) quotes
- **`TODO` Comments:** Use `TODO(username): Fix this.` format.
- **Imports Formatting:** Imports should be on separate lines and grouped:
  standard library, third-party, and your own application's imports.
- **In line comments:** Use `#` for single line comments. If a single line
  comment is longer than 80 characters, it should be split into multiple lines.
  Finally, if a comment follows a line of code, it should be separated by at
  least 2 spaces.

## 3. Naming
- **General:** `snake_case` for modules, functions, methods, and variables.
- **Classes:** `PascalCase`.
- **Constants:** `ALL_CAPS_WITH_UNDERSCORES`.
- **Internal Use:** Use a single leading underscore (`_internal_variable`)
  for internal module/class members.

## 4. Main
- All executable files should have a `main()` function that contains the
  main logic, called from a `if __name__ == '__main__':` block.

**BE CONSISTENT.** When editing code, match the existing style.

*Source: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)*

## 5. Unit Tests
- **BDD Styled Test Comments:** When creating a unit test, the pydoc for the
  tests function should follow the BDD format:
```python
"""One line description of what is being tested (i.e, "Tests an exception...")

Given a pre-condition or pre-requisite (ie, "Given a decimal input")
When the function under test is called (ie, "When the rounding function is
  called").
Then the following occurs (ie, "Then rounded up integer is returned")
"""
```
- **Behavioral Steps**: Finally, the steps should be descriptive of behavior,
  they should not describe implementation details. For example, saying "Then
  data is copied from the target to the source data source" is preferred over
  saying "Then the copy_data function is called with source table name and
  target table name."

- **Only test public functions/methods:**
  When creating a unit test, DO NOT directly test private functions (those
  functions with a starting underscore, "_"). Tests should only call public
  functions in the action phase of the test.
