// backend/src/types/types.ts
export interface IUser {
  _id: string;
  name: string;
  email: string;
  password: string;
  profile?: {
    location?: string;
    avatarUrl?: string;
    bio?: string;
  };
}

export interface IMushroom {
  _id: string;
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
  favorites: { userId: string; favoritedAt: Date }[];
}

export interface IBlogPost {
  _id: string;
  title: string;
  author: string;
  content: string;
  date: Date;
  imageUrl: string | null;
}

export interface IFavorite {
  _id: string;
  userId: string;
  mushroomId: string;
  favoritedAt: Date;
}
// backend/src/types/types.ts
export interface IUser {
  _id: string;
  name: string;
  email: string;
  password: string;
  profile?: {
    location?: string;
    avatarUrl?: string;
    bio?: string;
  };
}

export interface IMushroom {
  _id: string;
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
  favorites: { userId: string; favoritedAt: Date }[];
}

export interface IBlogPost {
  _id: string;
  title: string;
  author: string;
  content: string;
  date: Date;
  imageUrl: string | null;
}

export interface IFavorite {
  _id: string;
  userId: string;
  mushroomId: string;
  favoritedAt: Date;
}

