export interface Mushroom {
  _id: string;
  scientific_name: string;
  common_name?: string;
  authority?: string;
  classification: {
    kingdom?: string;
    phylum?: string;
    class_name?: string;
    order?: string;
    family?: string;
  };
  description: {
    general?: string;
    diagnostic?: string;
    habitat?: string;
    distribution?: string;
    uses?: string;
    look_alikes?: string;
  };
  image?: {
    url: string;
    copyright: string;
    license_url?: string;
  };
  regional_distribution?: {
    countries: string[];
    states: string[];
    regions?: string[];
  };
  observation_data?: {
    count: number;
    confidence?: number;
    first_observed?: string;
    last_observed?: string;
  };
  references?: string[];
}

export type MushroomFilter = {
  scientific_name?: string;
  common_name?: string;
  family?: string;
  habitat?: string;
  country?: string;
  state?: string;
}
