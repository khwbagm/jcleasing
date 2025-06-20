# Apartment Units Dashboard

A single-page application for visualizing apartment unit data.

## Features

- View all available apartment units in a sortable and filterable table
- Filter units by building, floorplan type, price range, and availability date
- View detailed information about each unit, including price history
- Responsive design that works on desktop and mobile devices
- Dark/light theme support

## Prerequisites

- Node.js (v16 or later)
- npm (v7 or later) or yarn

## Getting Started

1. **Install dependencies**:

   ```bash
   cd data_display
   npm install
   ```

2. **Copy the latest data file**:

   Run the following command to copy the most recent units data file to the public directory:

   ```bash
   npm run copy-data
   ```

   Or, to automatically copy the data and start the development server in one command:

   ```bash
   npm run dev:with-data
   ```

3. **Start the development server**:

   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build the application for production
- `npm run preview` - Preview the production build locally
- `npm run copy-data` - Copy the latest units data file to the public directory
- `npm run dev:with-data` - Copy the latest data and start the development server

## Project Structure

```
data_display/
├── public/                  # Static files
│   └── data/                # Data files
│       └── units.json        # Units data (copied from results/)
├── src/
│   ├── components/          # Reusable Vue components
│   ├── router/              # Vue Router configuration
│   ├── stores/              # Pinia stores
│   ├── types/               # TypeScript type definitions
│   ├── views/               # Page components
│   ├── App.vue              # Root component
│   └── main.ts              # Application entry point
├── scripts/
│   └── copy-data.js        # Script to copy the latest data file
├── index.html               # Main HTML file
├── package.json             # Project configuration
├── tsconfig.json            # TypeScript configuration
└── vite.config.ts           # Vite configuration
```

## Data Format

The application expects the units data to be in the following format:

```typescript
interface PriceInfo {
  price: string | number;
  price_range: string;
  date_fetched: string;
}

interface UnitInfo {
  unit: string;
  building: string;
  size: string | number;
  available_date: string;
  floorplan_type: string;
  floorplan_link: string;
  floorplan_note: string;
  prices: PriceInfo[];
}
```

## License

MIT
