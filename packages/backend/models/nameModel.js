import mongoose from 'mongoose';

const nameSchema = new mongoose.Schema({
  id: { type: Number, unique: true }, 
  name: String,
  author: String,
  rank: String,
  // ... other relevant fields from name responses ...
  createdAt: { type: Date, default: Date.now },
});

const Name = mongoose.model('Name', nameSchema);

export default Name;
