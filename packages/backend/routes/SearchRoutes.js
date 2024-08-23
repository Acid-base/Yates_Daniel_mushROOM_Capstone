import express from 'express';
import Observation from '../mongo/models/Observation';

const router = express.Router();

// Search observations by name
router.get('/observations', async (req, res) => {
  try {
    const searchTerm = req.query.q;

    if (!searchTerm) {
      return res.status(400).json({ error: 'Missing search term' });
    }

    const observations = await Observation.find({
      name: { $regex: new RegExp(searchTerm, 'i') }, // Case-insensitive regex search
    }).lean();

    res.json(observations);
  } catch (error) {
    console.error('Error searching observations:', error);
    res.status(500).json({ error: 'Failed to search observations' });
  }
});

export default router;
