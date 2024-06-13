// validators/validateMushroom.js  (or validateMushroom.cjs)

const Joi = require('joi'); // CommonJS import for Joi

const mushroomSchema = Joi.object({
  scientificName: Joi.string().required(),
  commonName: Joi.string().required(),
  edibility: Joi.string().valid('edible', 'inedible', 'poisonous').required(),
  // Add more fields as needed
});

const validateMushroom = (mushroom) => {
  const { error } = mushroomSchema.validate(mushroom);
  if (error) {
    throw new Error(`Validation error: ${error.details.map((detail) => detail.message).join(', ')}`);
  }
};

module.exports = validateMushroom; // CommonJS export
