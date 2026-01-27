## Running Locally

To run this project on your local machine, please follow these steps:

### Prerequisites

Make sure you have [Node.js](https://nodejs.js/) installed on your machine
(version 20 or later is recommended). `npm` (Node PackageManager) is
included with the Node.js installation.

### 1. Install Dependencies

Install all the required packages using npm:

```bash
npm ci
```

### 3. Run the Development Server

Start the Next.js development server:

```bash
npm run dev
```

### 4. View Your Application

Once the server starts, you will see output in your terminal indicating that
the app is running. You can now open your web browser and navigate to:

```
http://localhost:9002
```

## Known Issues

### Hydration Issue on Initial Load

Currently, after the initial load of the application, the interactive elements on the page may not function correctly until the page is manually refreshed. This is a known hydration issue that is actively being investigated.

**Workaround:** After the page loads, simply refresh your browser. All interactive elements should then work as expected.

### Mock Data (`data.json`)

This project uses a mock database for local development.

- **File:** `src/lib/data.json`
- **Purpose:** Acts as a temporary, file-based database to store and
  retrieve application data (e.g., reports).
- **How it works:** The server-side functions in `src/lib/actions.ts` read
  from and write to this file to simulate database operations.

When you are ready to connect to a real database (like Firebase Firestore,
a REST API, etc.), you can delete `src/lib/data.json`.

You will need to update the data-fetching functions (`getReports`,
`getReportById`, `createReport`, etc.) in `src/lib/actions.ts` to
interact with your live backend service instead of the local JSON file.

### TO DO List

1. Add docstrings to all exported functions.

2. Add unit tests to verify all logic in the application, even if it involves
   returning UI code (ie, HTML), using the `ui.text` testing module.

3. Fix docstrings to use `@return` instead of `@returns`.
