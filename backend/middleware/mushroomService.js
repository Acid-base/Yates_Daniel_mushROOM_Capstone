import axios from 'axios';
import Mushroom from '../models/MushroomModel'; // Assuming you have a Mushroom model

// ... (Your MongoDB connection setup)

async function fetchAndStoreMushroomData(scientificNames) {
  try {
    for (const scientificName of scientificNames) {
      // Fetch data from the API
      const nameResponse = await axios.get(
        `https://mushroomobserver.org/api2/names?name=${scientificName}`,
        { headers: { 'Accept': 'application/json' } }
      );
      const speciesResponse = await axios.get(
        `https://mushroomobserver.org/api2/species?name=${scientificName}`,
        { headers: { 'Accept': 'application/json' } }
      );
      const observationResponse = await axios.get(
        `https://mushroomobserver.org/api2/observations?name=${scientificName}`,
        { headers: { 'Accept': 'application/json' } }
      );

      // Check for API errors (e.g., status codes 400, 404, 500)
      if (
        !nameResponse.ok ||
        !speciesResponse.ok ||
        !observationResponse.ok
      ) {
        throw new Error(
          `API request failed with status ${response.status}: ${response.statusText}`
        );
      }

      // Combine data from different endpoints
      const nameData = nameResponse.data[0];
      const speciesData = speciesResponse.data[0];
      const observationData = observationResponse.data[0];

      const combinedData = {
        ...nameData,
        ...speciesData,
        ...observationData,
        // Add any additional data transformations or mappings here
      };

      // Check for data consistency (ensure uniqueness)
      const existingMushroom = await Mushroom.findOne({ scientificName });
      if (existingMushroom) {
        console.log(
          `Mushroom with scientific name ${scientificName} already exists. Skipping.`
        );
        continue; // Skip saving if it already exists
      }
      // Create a new Mushroom document
      const mushroom = new Mushroom(combinedData);

      // Save the document to MongoDB
      await mushroom.save();
      console.log(`Mushroom data saved for ${scientificName}`);
    }
  } catch (error) {
    console.error(`Error fetching data:`, error);
  }
}

// ... (Your MongoDB connection setup)

// Example scientific names
const scientificNames = ['Amanita muscaria', 'Boletus edulis', 'Cantharellus cibarius'];
// Make the initial request
fetchAndStoreMushroomData(scientificNames);

// Set up a timer to make requests every 10 seconds
setInterval(async () => {
  await fetchAndStoreMushroomData(scientificNames);
}, 10000);

export default fetchAndStoreMushroomData;
