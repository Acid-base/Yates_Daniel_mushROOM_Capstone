import fetchMushroomData from './apiHelper';

const fetchObservationImages = async (observationId) => {
  return await fetchMushroomData(`observations/${observationId}/images`, { format: 'json' });
};

const fetchObservationDetails = async (observationId) => {
  return await fetchMushroomData(`observations/${observationId}`, { detail: 'high', format: 'json' });
};

const fetchMushroomNames = async (params = {}) => {
  return await fetchMushroomData('names', { ...params, format: 'json' });
};

export { fetchObservationImages, fetchObservationDetails, fetchMushroomNames };
