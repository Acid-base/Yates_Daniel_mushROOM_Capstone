const mongoose = require('mongoose');

const mushroomSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['Edible', 'Poisonous', 'Unknown'],
    default: 'Unknown'
  }
  // ...other fields...
});

module.exports = mongoose.model('Mushroom', mushroomSchema);
