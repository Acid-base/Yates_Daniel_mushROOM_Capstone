import express from 'express';
import { fetchObservationDetails, fetchObservationImages } from '../utils/apiRequests';
import Observation from '../mongo/models/Observation';

const router = express.Router();

// Get all observations (with pagination)
router.get('/', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    const observations = await Observation.find()
      .skip(skip)
      .limit(limit)
      .lean();

    const totalObservations = await Observation.countDocuments();

    res.json({
      observations,
      currentPage: page,
      totalPages: Math.ceil(totalObservations / limit),
    });
  } catch (error) {
    console.error('Error fetching observations:', error);
    res.status(500).json({ error: 'Failed to fetch observations' });
  }
});

// Get observation details by ID
router.get('/:id', async (req, res) => {
  try {
    const observationId = parseInt(req.params.id);
    const observation = await Observation.findOne({ id: observationId }).lean();

    if (!observation) {
      return res.status(404).json({ error: 'Observation not found' });
    }

    res.json(observation);
  } catch (error) {
    console.error('Error fetching observation details:', error);
    res.status(500).json({ error: 'Failed to fetch observation details' });
  }
});

// Get images for an observation
router.get('/:id/images', async (req, res) => {
  try {
    const observationId = parseInt(req.params.id);
    const images = await fetchObservationImages(observationId);

    res.json(images.results); // Assuming the API response has a 'results' array
  } catch (error) {
    console.error('Error fetching images:', error);
    res.status(500).json({ error: 'Failed to fetch images' });
  }
});

export default router;
