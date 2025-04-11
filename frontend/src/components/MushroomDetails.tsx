import { ChevronLeftIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import {
    AspectRatio,
    Box,
    Button,
    Flex,
    Grid,
    GridItem,
    Heading,
    Image,
    Link,
    List,
    ListItem,
    Stack,
    Tag,
    Text,
    useColorModeValue,
} from '@chakra-ui/react';
import placeholderImage from '../assets/placeholder.svg';
import { Mushroom } from '../types/mushroom';

interface MushroomDetailsProps {
  mushroom: Mushroom;
  onBack: () => void;
}

const MushroomDetails = ({ mushroom, onBack }: MushroomDetailsProps) => {
  const defaultImage = placeholderImage;

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      bg={bgColor}
      p={6}
      borderRadius="lg"
      boxShadow="md"
      borderWidth="1px"
      borderColor={borderColor}
    >
      <Button
        leftIcon={<ChevronLeftIcon />}
        onClick={onBack}
        mb={4}
        size="sm"
        variant="outline"
      >
        Back to list
      </Button>

      <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={6}>
        {/* Left column: Image and basic info */}
        <GridItem>
          <AspectRatio ratio={4/3} mb={4}>
            <Image
              src={mushroom.image?.url || defaultImage}
              alt={mushroom.scientific_name}
              borderRadius="md"
              objectFit="cover"
            />
          </AspectRatio>

          {mushroom.image?.copyright && (
            <Text fontSize="xs" color="gray.500" mb={4}>
              Image: {mushroom.image.copyright}
            </Text>
          )}

          <Stack spacing={4}>
            <Box>
              <Heading size="lg" fontStyle="italic">{mushroom.scientific_name}</Heading>
              {mushroom.common_name && (
                <Heading size="md" fontWeight="normal" mt={1}>{mushroom.common_name}</Heading>
              )}
              {mushroom.authority && (
                <Text fontSize="sm" color="gray.600">{mushroom.authority}</Text>
              )}
            </Box>

            <Box>
              <Heading size="sm" mb={2}>Classification</Heading>
              <List spacing={1}>
                {mushroom.classification?.kingdom && (
                  <ListItem fontSize="sm">
                    <Text as="span" fontWeight="bold">Kingdom:</Text> {mushroom.classification.kingdom}
                  </ListItem>
                )}
                {mushroom.classification?.phylum && (
                  <ListItem fontSize="sm">
                    <Text as="span" fontWeight="bold">Phylum:</Text> {mushroom.classification.phylum}
                  </ListItem>
                )}
                {mushroom.classification?.class_name && (
                  <ListItem fontSize="sm">
                    <Text as="span" fontWeight="bold">Class:</Text> {mushroom.classification.class_name}
                  </ListItem>
                )}
                {mushroom.classification?.order && (
                  <ListItem fontSize="sm">
                    <Text as="span" fontWeight="bold">Order:</Text> {mushroom.classification.order}
                  </ListItem>
                )}
                {mushroom.classification?.family && (
                  <ListItem fontSize="sm">
                    <Text as="span" fontWeight="bold">Family:</Text> {mushroom.classification.family}
                  </ListItem>
                )}
              </List>
            </Box>

            {mushroom.observation_data && (
              <Box>
                <Heading size="sm" mb={2}>Observations</Heading>
                <Flex gap={4}>
                  <Box>
                    <Text fontSize="sm" fontWeight="bold">Count</Text>
                    <Text>{mushroom.observation_data.count}</Text>
                  </Box>
                  {mushroom.observation_data.confidence && (
                    <Box>
                      <Text fontSize="sm" fontWeight="bold">Confidence</Text>
                      <Text>{mushroom.observation_data.confidence.toFixed(2)}</Text>
                    </Box>
                  )}
                </Flex>
                <Flex gap={4} mt={2}>
                  {mushroom.observation_data.first_observed && (
                    <Box>
                      <Text fontSize="sm" fontWeight="bold">First Observed</Text>
                      <Text>{new Date(mushroom.observation_data.first_observed).toLocaleDateString()}</Text>
                    </Box>
                  )}
                  {mushroom.observation_data.last_observed && (
                    <Box>
                      <Text fontSize="sm" fontWeight="bold">Last Observed</Text>
                      <Text>{new Date(mushroom.observation_data.last_observed).toLocaleDateString()}</Text>
                    </Box>
                  )}
                </Flex>
              </Box>
            )}
          </Stack>
        </GridItem>

        {/* Right column: Descriptions */}
        <GridItem>
          <Stack spacing={6}>
            {mushroom.description?.general && (
              <Box>
                <Heading size="sm" mb={2}>General Description</Heading>
                <Text>{mushroom.description.general}</Text>
              </Box>
            )}

            {mushroom.description?.diagnostic && (
              <Box>
                <Heading size="sm" mb={2}>Diagnostic Features</Heading>
                <Text>{mushroom.description.diagnostic}</Text>
              </Box>
            )}

            {mushroom.description?.habitat && (
              <Box>
                <Heading size="sm" mb={2}>Habitat</Heading>
                <Text>{mushroom.description.habitat}</Text>
              </Box>
            )}

            {mushroom.description?.distribution && (
              <Box>
                <Heading size="sm" mb={2}>Distribution</Heading>
                <Text>{mushroom.description.distribution}</Text>
              </Box>
            )}

            {mushroom.regional_distribution && (
              <Box>
                <Heading size="sm" mb={2}>Regional Distribution</Heading>
                <Box mb={2}>
                  {mushroom.regional_distribution.countries?.map(country => (
                    <Tag key={country} mr={2} mb={2}>{country}</Tag>
                  ))}
                </Box>
                {mushroom.regional_distribution.states?.length > 0 && (
                  <Box>
                    <Text fontSize="sm" fontWeight="bold">States:</Text>
                    <Box>
                      {mushroom.regional_distribution.states.map(state => (
                        <Tag key={state} mr={2} mb={2} size="sm" variant="outline">{state}</Tag>
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            )}

            {mushroom.description?.look_alikes && (
              <Box>
                <Heading size="sm" mb={2}>Look-alikes</Heading>
                <Text>{mushroom.description.look_alikes}</Text>
              </Box>
            )}

            {mushroom.description?.uses && (
              <Box>
                <Heading size="sm" mb={2}>Uses</Heading>
                <Text>{mushroom.description.uses}</Text>
              </Box>
            )}

            {mushroom.references && mushroom.references.length > 0 && (
              <Box>
                <Heading size="sm" mb={2}>References</Heading>
                <List spacing={1}>
                  {mushroom.references.map((ref, index) => (
                    <ListItem key={index} fontSize="sm">
                      <Link href={ref} isExternal color="blue.500">
                        {ref.substring(0, 50)}... <ExternalLinkIcon mx="2px" />
                      </Link>
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </Stack>
        </GridItem>
      </Grid>
    </Box>
  );
};

export default MushroomDetails;
