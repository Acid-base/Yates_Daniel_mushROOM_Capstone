const mapObservation = (observation) => {
  const get = (obj, path, defaultValue = null) => {
    try {
      return path.split('.').reduce((acc, key) => acc && acc[key], obj);
    } catch (error) {
      return defaultValue;
    }
  };

  // Basic validation example (check if id and date are present)
  if (!observation.id || !observation.date) {
    console.error('Invalid observation data:', observation);
    return null; // Or throw an error to stop execution
  }

  return {
    id: observation.id,
    type: observation.type || null,
    date: get(observation, 'date') ? new Date(observation.date) : null,
    gps_hidden: observation.gps_hidden || false,
    specimen_available: observation.specimen_available || false,
    is_collection_location: observation.is_collection_location || false,
    created_at: get(observation, 'created_at') ? new Date(observation.created_at) : null,
    updated_at: get(observation, 'updated_at') ? new Date(observation.updated_at) : null,
    number_of_views: observation.number_of_views || 0,
    last_viewed: get(observation, 'last_viewed') ? new Date(observation.last_viewed) : null,
    notes: observation.notes || null,
    owner: {
      userId: get(observation, 'owner.id'),
      username: get(observation, 'owner.login_name')
    },
    consensus: {
      id: get(observation, 'consensus.id'),
      name: get(observation, 'consensus.name')
    },
    namings: get(observation, 'namings', []).map(naming => get(naming, 'name.name')) || [],
    votes: {
      total: get(observation, 'votes.total', 0),
      votes: get(observation, 'votes.votes', [])
    },
    location: observation.location ? {
      locationId: get(observation, 'location.id'),
      locationName: get(observation, 'location.name'),
      latitude: get(observation, 'location.latitude_north'),
      longitude: get(observation, 'location.longitude_east'),
      region: get(observation, 'location.region')
    } : null,
    primary_image: {
      id: get(observation, 'primary_image.id'),
      url: get(observation, 'primary_image.original_url')
    },
    images: get(observation, 'images')
      ? get(observation, 'images').map(image => image.original_url)
      : [],
  };
};

export default mapObservation;
