import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import {
  Box,
  ChakraProvider,
  Container,
  Flex,
  Grid,
  GridItem,
  Heading,
  HStack,
  IconButton,
  SimpleGrid,
  Spinner,
  Text
} from '@chakra-ui/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { FilterSidebar } from './components/FilterSidebar';
import MushroomCard from './components/MushroomCard';
import MushroomDetails from './components/MushroomDetails';
import { useMushrooms } from './hooks/useMushrooms';
import { queryClient } from './queryClient';
import theme from './theme';
import { Mushroom, MushroomFilter } from './types/mushroom';
import Header from './components/Header.tsx';

function App() {
  const [selectedMushroom, setSelectedMushroom] = useState<Mushroom | null>(null);
  const [currentFilter, setCurrentFilter] = useState<MushroomFilter>({});
  const [currentPage, setCurrentPage] = useState(0);
  const itemsPerPage = 12;

  const {
    mushrooms,
    isLoading,
    isError,
    error,
    totalCount,
    totalPages,
    isFetching
  } = useMushrooms(currentFilter, currentPage, itemsPerPage);

  const handleCardClick = (mushroom: Mushroom) => {
    setSelectedMushroom(mushroom);
    window.scrollTo(0, 0);
  };

  const handleBack = () => {
    setSelectedMushroom(null);
  };

  const handleFilterChange = (newFilter: MushroomFilter) => {
    setCurrentFilter(newFilter);
    setCurrentPage(0); // Reset to first page when filter changes
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
      window.scrollTo(0, 0);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
      window.scrollTo(0, 0);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider theme={theme}>
        <Box minH="100vh" bg="gray.50">
          <Header />

          <Container maxW="container.xl" py={8}>
            {selectedMushroom ? (
              <MushroomDetails
                mushroom={selectedMushroom}
                onBack={handleBack}
              />
            ) : (
              <Grid templateColumns={{ base: "1fr", md: "250px 1fr" }} gap={6}>
                <GridItem>
                  <FilterSidebar onFilterChange={handleFilterChange} />
                </GridItem>

                <GridItem>
                  <Box mb={4}>
                    <Flex justifyContent="space-between" alignItems="center">
                      <Heading size="lg">Mushroom Field Guide</Heading>
                      {totalCount > 0 && (
                        <Text fontSize="sm" color="gray.600">
                          Showing {currentPage * itemsPerPage + 1}-{Math.min((currentPage + 1) * itemsPerPage, totalCount)} of {totalCount} mushrooms
                        </Text>
                      )}
                    </Flex>
                  </Box>

                  {isLoading ? (
                    <Flex justify="center" align="center" h="300px">
                      <Spinner size="xl" color="mushroom.500" />
                    </Flex>
                  ) : isError ? (
                    <Box p={4} bg="red.50" color="red.500" borderRadius="md">
                      Error: {error instanceof Error ? error.message : 'An error occurred while fetching mushrooms'}
                    </Box>
                  ) : mushrooms.length === 0 ? (
                    <Box p={8} textAlign="center" bg="white" borderRadius="md" boxShadow="sm">
                      <Text fontSize="lg">No mushrooms found matching your criteria.</Text>
                      <Text fontSize="md" mt={2} color="gray.600">Try adjusting your filters.</Text>
                    </Box>
                  ) : (
                    <>
                      <SimpleGrid columns={{ base: 1, sm: 2, lg: 3 }} spacing={6}>
                        {mushrooms.map((mushroom) => (
                          <MushroomCard
                            key={mushroom._id}
                            mushroom={mushroom}
                            onClick={handleCardClick}
                          />
                        ))}
                      </SimpleGrid>

                      {totalPages > 1 && (
                        <Flex justifyContent="center" mt={8}>
                          <HStack>
                            <IconButton
                              aria-label="Previous page"
                              icon={<ChevronLeftIcon />}
                              onClick={handlePrevPage}
                              isDisabled={currentPage === 0}
                            />

                            <Text px={4}>
                              Page {currentPage + 1} of {totalPages}
                            </Text>

                            <IconButton
                              aria-label="Next page"
                              icon={<ChevronRightIcon />}
                              onClick={handleNextPage}
                              isDisabled={currentPage === totalPages - 1}
                            />
                          </HStack>
                        </Flex>
                      )}
                    </>
                  )}

                  {/* Loading indicator for subsequent fetches */}
                  {!isLoading && isFetching && (
                    <Flex justify="center" mt={4}>
                      <Spinner size="sm" color="mushroom.500" />
                    </Flex>
                  )}
                </GridItem>
              </Grid>
            )}
          </Container>
        </Box>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;
