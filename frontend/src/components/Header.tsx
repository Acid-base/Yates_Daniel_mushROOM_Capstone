import { Box, Container, Flex, Heading, Text, useColorModeValue } from '@chakra-ui/react';

const Header = () => {
  return (
    <Box 
      as="header" 
      bg={useColorModeValue('mushroom.500', 'mushroom.700')} 
      color="white"
      py={4} 
      position="sticky" 
      top={0} 
      zIndex={10}
      boxShadow="md"
    >
      <Container maxW="container.xl">
        <Flex justify="space-between" align="center">
          <Flex align="center">
            <Heading size="lg">🍄 mushROOM</Heading>
          </Flex>
          <Text fontSize="sm">Mushroom Field Guide</Text>
        </Flex>
      </Container>
    </Box>
  );
};

export default Header;
