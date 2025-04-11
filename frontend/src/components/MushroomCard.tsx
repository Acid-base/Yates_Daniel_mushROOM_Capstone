import {
    Badge,
    Box,
    Card,
    CardBody,
    CardFooter,
    Flex,
    Heading,
    Image,
    Stack,
    Text,
    useColorModeValue
} from '@chakra-ui/react';
import placeholderImage from '../assets/placeholder.svg';
import { Mushroom } from '../types/mushroom';

interface MushroomCardProps {
  mushroom: Mushroom;
  onClick: (mushroom: Mushroom) => void;
}

const MushroomCard = ({ mushroom, onClick }: MushroomCardProps) => {
  // Default image for mushrooms without an image (using local asset)
  const defaultImage = placeholderImage;

  return (
    <Card
      maxW="sm"
      cursor="pointer"
      onClick={() => onClick(mushroom)}
      _hover={{ transform: 'translateY(-5px)', transition: 'transform 0.3s' }}
      overflow="hidden"
      borderRadius="lg"
      boxShadow="md"
      bg={useColorModeValue('white', 'gray.700')}
    >
      <Image
        objectFit="cover"
        maxH="200px"
        width="100%"
        src={mushroom.image?.url || defaultImage}
        alt={mushroom.scientific_name}
      />
      <CardBody>
        <Stack spacing="3">
          <Heading size="md" fontStyle="italic">
            {mushroom.scientific_name}
          </Heading>

          {mushroom.common_name && (
            <Text fontSize="sm" color="gray.500">
              {mushroom.common_name}
            </Text>
          )}

          <Flex gap={2} flexWrap="wrap">
            {mushroom.classification?.family && (
              <Badge colorScheme="green" variant="subtle">
                {mushroom.classification.family}
              </Badge>
            )}

            {mushroom.description?.habitat && (
              <Badge colorScheme="blue" variant="subtle">
                Habitat: {mushroom.description.habitat.substring(0, 30)}...
              </Badge>
            )}
          </Flex>
        </Stack>
      </CardBody>
      <CardFooter pt={0}>
        <Box fontSize="xs">
          {mushroom.observation_data && (
            <Flex gap={2}>
              <Text>🔍 {mushroom.observation_data.count} observations</Text>
              {mushroom.observation_data.confidence && (
                <Text>⭐ {mushroom.observation_data.confidence.toFixed(1)}</Text>
              )}
            </Flex>
          )}
        </Box>
      </CardFooter>
    </Card>
  );
};

export default MushroomCard;
