MAGI System Demo
======

# MAGI Frontend

This is the frontend application for MAGI project built with Next.js.

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn

## Getting Started

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Run the development server:
```bash
npm run dev
# or
yarn dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Build for Production

To build the application for production:

```bash
npm run build
# or
yarn build
```

Then start the production server:

```bash
npm run start
# or
yarn start
```

## Docker Support

You can also run the frontend using Docker:

```bash
docker build -t magi-frontend .
docker run -p 3000:3000 magi-frontend
