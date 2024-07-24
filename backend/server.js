import express from 'express';
import mongoose from './mongo/db';
import apiLimiter from './middleware/rateLimiter';
import observationsRouter from './routes/observations';
import namesRouter from './routes/names';
import searchRouter from './routes/search';
import { storeObservations, storeImages, storeNames } from './utils/dataStorage';
import mapObservation from './utils/dataMapper';
import { fetchObservationImages, fetchObservationDetails, fetchMushroomNames } from './utils/apiRequests';

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(express.json());
app.use(apiLimiter);

// Routes
app.use('/api/observations', observationsRouter);
app.use('/api/names', namesRouter);
app.use('/api/search', searchRouter);

// Start your server 
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

// --- Data Fetching and Storage Logic ---

async function fetchAndStorePage(currentPage) {
  try {
    const observationsData = await fetchObservationDetails(currentPage);

    console.log(`API Response (Page ${currentPage}):`);
    console.dir(observationsData, { depth: null });

    // Check for API errors FIRST
    if (observationsData && observationsData.error) {
      console.error(`API Error (Page ${currentPage}):`, observationsData.error);
      return false; // Stop fetching if there's an API error
    }

    // THEN, check if results are present
    if (observationsData && Array.isArray(observationsData.results) && observationsData.results.length > 0) {
      try {
        const observations = observationsData.results.map(mapObservation).filter(obs => obs !== null);
        await storeObservations(observations);

        const imagePromises = observations.map(obs => fetchObservationImages(obs.id).then(images => storeImages(images.results)));
        await Promise.all(imagePromises);

        return true; // Continue fetching if successful
      } catch (mappingError) {
        console.error(`Error mapping observations (Page ${currentPage}):`, mappingError);
        return false; // Stop fetching if there's a mapping error
      }
    } else { // Only print "No more observations..." if there's no error AND no results
      console.log(`No more observations found after page ${currentPage - 1}.`);
      return false; // Stop fetching if no more results
    }

  } catch (fetchError) {
    console.error(`Error fetching data for page ${currentPage}:`, fetchError);
    return true; // CONTINUE FETCHING even if there's a fetch error (likely temporary)
  }
}

async function continuousFetch() {
  let currentPage = 1;

  while (await fetchAndStorePage(currentPage)) {
    currentPage++;
    await new Promise(resolve => setTimeout(resolve, 5000)); 
  }

  setInterval(async () => {
    if (await fetchAndStorePage(currentPage)) {
      currentPage++;
    }
  }, 3600000); 
}

let initialDataFetched = false; 

async function fetchInitialData() {
  if (initialDataFetched) {
    console.log("Initial data already fetched. Skipping.");
    return;
  }

  let currentPage = 1;
  const maxPages = 10; // Adjust as needed

  while (currentPage <= maxPages && await fetchAndStorePage(currentPage)) {
    currentPage++;
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  // Fetch and store names 
  const namesData = await fetchMushroomNames();
  if (namesData && namesData.results && namesData.results.length > 0) { 
    await storeNames(namesData.results);
  }

  initialDataFetched = true;
}

// Start continuous fetching
continuousFetch();

// Fetch initial data on startup
fetchInitialData();
