import mongoose from '../mongo/db';
import { fetchObservationImages, fetchObservationDetails, fetchMushroomNames } from '../utils/apiRequests';
import { storeObservations, storeImages, storeNames } from '../utils/dataStorage';
import mapObservation from '../utils/dataMapper';

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

async function populateMushrooms() {
  let currentPage = 1;

  while (await fetchAndStorePage(currentPage)) {
    currentPage++;
    await new Promise(resolve => setTimeout(resolve,

