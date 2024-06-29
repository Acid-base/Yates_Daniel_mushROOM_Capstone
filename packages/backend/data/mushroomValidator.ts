import Joi from 'joi';

const mushroomSchema = Joi.object({
  scientificName: Joi.string().required(),
  commonName: Joi.string().required(),
  edibility: Joi.string().valid('edible', 'inedible', 'poisonous').required(),
  // Add more fields as needed
});

const validateMushroom = (mushroom: any) => {
  const { error } = mushroomSchema.validate(mushroom);
  if (error) {
    throw new Error(
      `Validation error: ${error.details.map((detail) => detail.message).join(', ')}`,
    );
  }
};

export default validateMushroom;
