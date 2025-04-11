import {
    Box,
    Button,
    Divider,
    Flex,
    FormControl,
    FormLabel,
    Heading,
    Input,
    Select,
    VStack
} from '@chakra-ui/react';
import { useState } from 'react';
import { useDistinctValues } from '../hooks/useMushrooms';
import { MushroomFilter } from '../types/mushroom';

interface FilterSidebarProps {
  onFilterChange: (filter: MushroomFilter) => void;
}

export const FilterSidebar = ({ onFilterChange }: FilterSidebarProps) => {
  const [filter, setFilter] = useState<MushroomFilter>({});

  // Get distinct values for filter dropdowns
  const { data: families } = useDistinctValues('classification.family');
  const { data: countries } = useDistinctValues('regional_distribution.countries');

  // Handle input changes
  const handleInputChange = (field: keyof MushroomFilter, value: string) => {
    setFilter(prev => ({
      ...prev,
      [field]: value || undefined // Set to undefined if empty to remove from filter
    }));
  };

  // Apply filters
  const applyFilters = () => {
    onFilterChange(filter);
  };

  // Clear filters
  const clearFilters = () => {
    setFilter({});
    onFilterChange({});
  };

  return (
    <Box
      p={4}
      bg="white"
      borderRadius="md"
      boxShadow="sm"
      width="100%"
    >
      <VStack spacing={4} align="stretch">
        <Heading size="md">Filter Mushrooms</Heading>
        <Divider />

        <FormControl>
          <FormLabel>Scientific Name</FormLabel>
          <Input
            placeholder="e.g., Amanita"
            value={filter.scientific_name || ''}
            onChange={(e) => handleInputChange('scientific_name', e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Common Name</FormLabel>
          <Input
            placeholder="e.g., Chanterelle"
            value={filter.common_name || ''}
            onChange={(e) => handleInputChange('common_name', e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Family</FormLabel>
          <Select
            placeholder="Select family"
            value={filter.family || ''}
            onChange={(e) => handleInputChange('family', e.target.value)}
          >
            {families?.map(family => (
              <option key={family} value={family}>{family}</option>
            ))}
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Habitat</FormLabel>
          <Input
            placeholder="e.g., Forest"
            value={filter.habitat || ''}
            onChange={(e) => handleInputChange('habitat', e.target.value)}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Country</FormLabel>
          <Select
            placeholder="Select country"
            value={filter.country || ''}
            onChange={(e) => handleInputChange('country', e.target.value)}
          >
            {countries?.map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </Select>
        </FormControl>

        {filter.country === 'USA' && (
          <FormControl>
            <FormLabel>State</FormLabel>
            <Input
              placeholder="e.g., California"
              value={filter.state || ''}
              onChange={(e) => handleInputChange('state', e.target.value)}
            />
          </FormControl>
        )}

        <Flex gap={2} mt={2}>
          <Button colorScheme="mushroom" flexGrow={1} onClick={applyFilters}>
            Apply Filters
          </Button>
          <Button variant="outline" onClick={clearFilters}>
            Clear
          </Button>
        </Flex>
      </VStack>
    </Box>
  );
};

export default FilterSidebar;
