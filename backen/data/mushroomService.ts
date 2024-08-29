import axios from 'axios';
import rateLimit from 'axios-rate-limit';
import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import authenticateToken from '../../middleware/auth';
import Mushroom from '../../models/MushroomModel';
import blogRouter from '../routes/blogRoutes';
import mushroomRouter from '../routes/mushroomRoutes';
import userRoutes from '../routes/userRoutes';
import * as db from './db';

dotenv.config();

const app = express();
const port = process.env.PORT || 3008;

app.use(express.json());
app.use(cors());

const api = rateLimit(axios.create(), {
  maxRequests: 1,
  perMilliseconds: 6000,
});

app.use(authenticateToken);

app.use('/api/users', userRoutes);
app.use('/api/mushrooms', mushroomRouter);
app.use('/api/blogs', blogRouter);

async function fetchAndStoreMushroomData(observationId: number) {
  const observationUrl = `https://mushroomobserver.org/api2/observations?id=${observationId}&detail=high&format=json`;

  try {
    const response = await fetch(observationUrl);
    const data = await response.json();

    const observation = data.results[0];
    const mushroomData = {
      scientificName: observation.consensus_name,
      latitude: observation.location.gps.latitude,
      longitude: observation.location.gps.longitude,
      imageUrl: observation.primary_image_url,
      description: observation.notes,
      commonName: observation.name_common,
      family: observation.name_family,
      genus: observation.name_genus,
      region: observation.location.region,
      kingdom: observation.name_kingdom,
      phylum: observation.name_phylum,
      class: observation.name_class,
      order: observation.name_order,
      habitat: observation.habitat,
      edibility: observation.edibility,
      distribution: observation.distribution,
      mushroomObserverUrl: `https://mushroomobserver.org/observations/${observation.id}`,
    };

    const updatedMushroom = await Mushroom.findOneAndUpdate(
      { scientificName: mushroomData.scientificName },
      mushroomData,
      { upsert: true, new: true },
    );

    console.log('Mushroom data saved or updated successfully:', updatedMushroom);
  } catch (error) {
    console.error('Error fetching or saving mushroom data:', error);
  }
}

app.listen(port, async () => {
  try {
    await db.connectToDatabase();
    console.log(`Mushroom Explorer backend listening at http://localhost:${port}`);

    await fetchAndStoreMushroomData(12345);
  } catch (error) {
    console.error('Error starting the server:', error);
  }
});
