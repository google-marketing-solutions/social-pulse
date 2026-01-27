# UI Components (shadcn/ui)

This directory contains the source code for the UI components used throughout the application. These components are based on **shadcn/ui**.

## Why is the source code here?

Unlike traditional component libraries that are installed as dependencies from `npm` (e.g., Material-UI, Ant Design), shadcn/ui follows a different philosophy. Instead of importing from a package, you use a CLI tool to copy the source code for individual components directly into your project.

### Key Benefits:

1.  **Ownership and Control**: You own this code. You are free to modify any component to meet the specific needs of your application. You can change styles, add or remove props, and adjust behavior without limitations.
2.  **No "Black Box"**: The code is not hidden away in `node_modules`. It's part of your codebase, making it easy to understand, debug, and customize.
3.  **Lean and Mean**: This approach avoids adding another large dependency to your project. The components are built using libraries already in use (Radix UI and Tailwind CSS).

You can learn more about the philosophy behind this approach at the [shadcn/ui documentation](https://ui.shadcn.com/docs).
