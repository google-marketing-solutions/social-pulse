# TypeScript & UI Code Style Guide

This document outlines key rules and best practices for creating and modifying
TypeScript code in the Gemini Social Sentiment Analyzer project, primarily focusing on the Next.js
`report_service/ui` application.

## 1. General TypeScript Rules
- **Strict Typing:** Always use strong, explicit typing. Avoid `any`. Use
  interfaces and type aliases to define data shapes.
- **Variables:** Use `const` by default. Use `let` only when the variable's
  value must be reassigned. Never use `var`.
- **Functions:** Use standard function declarations (e.g.,
  `function MyComponent() {...}`) for components and simple helper functions.
  Avoid arrow functions for primary exports unless passing functions as props
  or closures. Ensure JSDoc comments correctly document props and parameters.
- **Imports:** Group imports logically: React/Next.js core first, third-party
  libraries second, internal components/utils third.

## 2. React & Next.js Best Practices
- **Components:** Create modular, functional components. Keep component files
  focused and maintainable.
- **Client vs Server Components:** Adhere to Next.js App Router principles.
  Components should be server components by default unless they require
  client-side interactivity or React hooks. In such cases, explicitly declare
  `"use client"` at the very top of the file.
- **Hooks:** Keep hook logic clean. Utilize custom hooks (`use*`) to extract
  complex business logic away from the UI presentation layer when appropriate.

## 3. Formatting & Styling
- **Aesthetics & Styling Systems:** Use Vanilla CSS/TailwindCSS per existing
  project patterns for dynamic, highly responsive styling. Modern aesthetics
  are expected (e.g. curated palettes, smooth gradients, subtle
  micro-interactions like hover states). Be mindful of existing visual choices
  (like rounded pill edges for charts and standardized padding).
- **Indentation & Spacing:** Use 2 spaces for indentation. Ensure your editor
  is configured to use spaces instead of tabs.
- **Semicolons:** Use trailing semicolons to prevent ASI (Automatic Semicolon
  Insertion) edge-cases.
- **Line Length:** Try to maintain 80 character line limits where possible for
  better readability.

## 4. Testing (Frontend)
- **Frameworks:** Rely on Jest and React Testing Library (RTL).
- **Scope:** Focus on testing the public interface and user interactions,
  rather than internal component implementation details.
- **Mocking:** Keep mocks targeted and use them to isolate the component under
  test.
