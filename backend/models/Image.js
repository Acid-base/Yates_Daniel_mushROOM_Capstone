const mongoose = require('mongoose'); // Import mongoose at the top 

const imageSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  content_type: { type: String, required: true },
  copyright_holder: { type: String, required: true },
  license: { type: String, required: true },
  ok_for_export: { type: Boolean, required: true },
  diagnostic: { type: Boolean, required: true },
  //  ... (other image fields)
  image_url: { type: String, required: false },
  observations: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Observation' }]
});

// Create indexes for efficient querying
imageSchema.index({ content_type: 1 });
imageSchema.index({ copyright_holder: 1 });

const Image = mongoose.model('Image', imageSchema);

module.exports = Image;
