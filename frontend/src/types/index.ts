// frontend/src/types/index.ts

export interface User {
  id: string;
  name: string;
  email: string;
  location?: string;
  avatarUrl?: string;
  bio?: string;
  favorites: Mushroom[];
  savedMushrooms: Mushroom[];
}

export interface Mushroom {
  scientificName: string;
  latitude: number;
  longitude: number;
  imageUrl: string;
  description?: string;
  commonName?: string;
  family?: string;
  genus?: string;
  region?: string;
  gallery?: { url: string; thumbnailUrl: string }[];
  kingdom?: string;
  phylum?: string;
  class?: string;
  order?: string;
  habitat?: string;
  edibility?: string;
  distribution?: string;
  wikipediaUrl?: string;
  mushroomObserverUrl?: string;
}

export interface APIError {
  error: string;
}
