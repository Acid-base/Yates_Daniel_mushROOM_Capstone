import mongoose from 'mongoose';

const observationSchema = new mongoose.Schema({
  id: { type: Number, unique: true },
  name: String,
  date: Date,
  locationId: Number,
  locationName: String,
  thumbnailUrl: String,
  latitude: Number,
  longitude: Number,
  imageUrl: String,
  description: String,
  commonName: String,
  family: String,
  genus: String,
  region: String,
  kingdom: String,
  phylum: String,
  class: String,
  order: String,
  habitat: String,
  edibility: String,
  distribution: String,
  mushroomObserverUrl: String,
  wikipediaUrl: String,
  owner: {
    userId: Number,
    username: String
  },
  consensus: {
    id: Number,
    name: String
  },
  namings: [String],
  votes: {
    total: Number,
    votes: [Object]
  },
  location: {
    locationId: Number,
    locationName: String,
    latitude: Number,
    longitude: Number,
    region: String,
  },
  primary_image: {
    id: Number,
    url: String,
  },
  images: [String],
  type: String,
  gps_hidden: Boolean,
  specimen_available: Boolean,
  is_collection_location: Boolean,
  created_at: Date,
  updated_at: Date,
  number_of_views: Number,
  last_viewed: Date,
  createdAt: { type: Date, default: Date.now },
});

const Observation = mongoose.model('Observation', observationSchema);

export default Observation;
