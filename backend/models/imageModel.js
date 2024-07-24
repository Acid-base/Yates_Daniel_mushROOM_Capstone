import mongoose from 'mongoose';

const imageSchema = new mongoose.Schema({
  id: { type: Number, unique: true }, 
  url: String,
  observationId: Number,
  createdAt: { type: Date, default: Date.now },
});

const Image = mongoose.model('Image', imageSchema);

export default Image;
