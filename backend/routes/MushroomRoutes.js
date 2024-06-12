// routes/MushroomRoutes.js
const express = require('express');
const router = express.Router(); 
const { body, validationResult } = require('express-validator');
const Mushroom = require('../models/MushroomModel'); 

router.post('/',
  [
    body('scientificName').notEmpty().trim().escape(),
    body('latitude').isFloat(),
    body('longitude').isFloat(),
    body('imageUrl').optional().isURL(),
    // ... add validation for other fields
  ],
  async (req, res) => {
    // ... (Your validation and mushroom creation logic from before)
  }
);

module.exports = router; 
