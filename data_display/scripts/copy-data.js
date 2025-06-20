const fs = require('fs');
const path = require('path');

// Create public/data directory if it doesn't exist
const publicDataDir = path.join(__dirname, '../public/data');
if (!fs.existsSync(publicDataDir)) {
  fs.mkdirSync(publicDataDir, { recursive: true });
}

// Find the most recent units file
const resultsDir = path.join(__dirname, '../../results');
let files = [];

try {
  files = fs.readdirSync(resultsDir)
    .filter(file => (file.startsWith('results_') || file.startsWith('daily-results_')) && file.endsWith('.json'))
    .sort()
    .reverse();
} catch (err) {
  console.error('Could not read results directory:', err.message);
  process.exit(1);
}

if (files.length === 0) {
  console.error('No unit data files found in the results directory');
  process.exit(1);
}

const latestFile = files[0];
const sourcePath = path.join(resultsDir, latestFile);
const destPath = path.join(publicDataDir, 'units.json');

try {
  // Copy the file
  fs.copyFileSync(sourcePath, destPath);
  console.log(`Copied ${latestFile} to public/data/units.json`);
  
  // Verify the file was copied and show its size
  const stats = fs.statSync(destPath);
  console.log(`File size: ${Math.round(stats.size / 1024)}KB`);
} catch (err) {
  console.error('Error copying file:', err.message);
  process.exit(1);
}
