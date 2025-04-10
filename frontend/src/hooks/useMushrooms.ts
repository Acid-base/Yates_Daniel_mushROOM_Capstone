import { useQuery } from '@tanstack/react-query';
import {
  countMushrooms,
  findMushroomById,
  findMushroomByScientificName,
  findMushrooms,
  getDistinctValues,
} from '../api/mongodb';
import { MushroomFilter } from '../types/mushroom';

// Hook to fetch mushrooms with optional filtering and pagination
export function useMushrooms(filter: MushroomFilter = {}, page = 0, limit = 10) {
  const skip = page * limit;

  const mushroomsQuery = useQuery({
    queryKey: ['mushrooms', filter, page, limit],
    queryFn: () => findMushrooms(filter, limit, skip),
  });

  const countQuery = useQuery({
    queryKey: ['mushrooms-count', filter],
    queryFn: () => countMushrooms(filter),
  });

  return {
    mushrooms: mushroomsQuery.data || [],
    isLoading: mushroomsQuery.isLoading,
    isError: mushroomsQuery.isError,
    error: mushroomsQuery.error,
    totalCount: countQuery.data || 0,
    totalPages: countQuery.data ? Math.ceil(countQuery.data / limit) : 0,
    isFetching: mushroomsQuery.isFetching || countQuery.isFetching,
  };
}

// Hook to fetch a single mushroom by ID
export function useMushroomById(id: string | null) {
  return useQuery({
    queryKey: ['mushroom', id],
    queryFn: () => findMushroomById(id!),
    enabled: !!id, // Only run the query if ID is provided
  });
}

// Hook to fetch a mushroom by scientific name
export function useMushroomByScientificName(name: string | null) {
  return useQuery({
    queryKey: ['mushroom', 'scientific', name],
    queryFn: () => findMushroomByScientificName(name!),
    enabled: !!name, // Only run the query if name is provided
  });
}

// Hook to fetch distinct values for a specific field
export function useDistinctValues(field: string) {
  return useQuery({
    queryKey: ['distinct', field],
    queryFn: () => getDistinctValues(field),
  });
}
