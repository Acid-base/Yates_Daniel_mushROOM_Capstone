# Mushroom Project pnpm Monorepo Guide

This guide explains how to work with the mushroom project monorepo using pnpm workspaces.

## Project Structure

```
mushroom-project/
├── package.json           # Root package.json with shared configs
├── pnpm-workspace.yaml    # Workspace configuration
├── frontend/              # React frontend with Chakra UI
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   └── ...
├── backend/               # Express API server
│   ├── package.json
│   ├── src/
│   │   └── ...
│   └── ...
└── workers/               # Cloudflare Workers
    ├── package.json       # Shared workers configs
    ├── image-processor/   # Image processing worker
    │   ├── package.json
    │   ├── wrangler.toml
    │   ├── src/
    │   │   └── ...
    │   └── ...
    └── ...
```

## Setup Instructions

1. **Install pnpm** (if not already installed):
   ```bash
   npm install -g pnpm
   ```

2. **Install dependencies** for all packages:
   ```bash
   pnpm install
   ```

3. **Set up environment variables**:
   - Create `.env` files in each package directory as needed
   - For Cloudflare Workers secrets:
     ```bash
     cd workers/image-processor
     pnpm wrangler secret put MONGODB_CONNECTION_STRING
     pnpm wrangler secret put R2_ACCOUNT_ID
     ```

## Development Commands

### Working with all packages

From the root directory:

- **Start development servers** for all packages:
  ```bash
  pnpm dev
  ```

- **Build all packages**:
  ```bash
  pnpm build
  ```

- **Run tests** across all packages:
  ```bash
  pnpm test
  ```

- **Lint all code**:
  ```bash
  pnpm lint
  ```

- **Format all code**:
  ```bash
  pnpm format
  ```

- **Clean up node_modules** and build artifacts:
  ```bash
  pnpm clean
  ```

### Working with specific packages

- **Run commands in a specific package**:
  ```bash
  pnpm --filter @mushroom/frontend dev
  pnpm --filter @mushroom/backend dev
  pnpm --filter @mushroom/image-processor dev
  ```

- **Add dependencies to a specific package**:
  ```bash
  pnpm --filter @mushroom/frontend add react-icons
  pnpm --filter @mushroom/backend add joi
  ```

- **Add dev dependencies to a specific package**:
  ```bash
  pnpm --filter @mushroom/frontend add -D vitest
  ```

## Package-Specific Instructions

### Frontend (React + Chakra UI)

1. **Start development server**:
   ```bash
   cd frontend
   pnpm dev
   ```

2. **Build for production**:
   ```bash
   cd frontend
   pnpm build
   ```

3. **Preview production build**:
   ```bash
   cd frontend
   pnpm preview
   ```

### Backend (Express + MongoDB)

1. **Start development server**:
   ```bash
   cd backend
   pnpm dev
   ```

2. **Build for production**:
   ```bash
   cd backend
   pnpm build
   ```

3. **Start production server**:
   ```bash
   cd backend
   pnpm start
   ```

### Workers (Cloudflare Workers)

#### Image Processor Worker

1. **Develop locally**:
   ```bash
   cd workers/image-processor
   pnpm dev
   ```

2. **Build for production**:
   ```bash
   cd workers/image-processor
   pnpm build
   ```

3. **Deploy to Cloudflare**:
   ```bash
   cd workers/image-processor
   pnpm publish
   ```

## Dependencies Between Packages

If you need to use code from one package in another:

1. **Add the dependency in package.json**:
   ```json
   "dependencies": {
     "@mushroom/shared": "workspace:*"
   }
   ```

2. **Import the code**:
   ```typescript
   import { someUtil } from '@mushroom/shared';
   ```

## Common Issues and Solutions

### Dependency Hoisting

pnpm uses strict dependency isolation by default. If you need to access a dependency that's not directly declared in your package.json, you'll need to hoist it:

Create a `.npmrc` file in the root:
```
shamefully-hoist=true
```

### Workspace Not Found

If you get "workspace not found" errors, ensure:
1. The package is correctly listed in pnpm-workspace.yaml
2. Package names in package.json match the format used in import statements

### Wrangler Configuration

If Wrangler has issues with the pnpm workspace:
1. Install wrangler globally: `pnpm add -g wrangler`
2. Use direct paths to wrangler in node_modules

## Deployment

### Frontend
```bash
cd frontend
pnpm build
# Deploy dist/ to your hosting provider
```

### Backend
```bash
cd backend
pnpm build
# Deploy dist/ to your server
```

### Cloudflare Workers
```bash
cd workers/image-processor
pnpm publish
```
