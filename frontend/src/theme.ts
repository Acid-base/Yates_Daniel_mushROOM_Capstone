import { extendTheme } from '@chakra-ui/react';

// Extend the default Chakra UI theme
const theme = extendTheme({
  colors: {
    mushroom: {
      50: '#f7f8ea',
      100: '#e5e7c5',
      200: '#d4d69e',
      300: '#c3c576',
      400: '#b3b54f',
      500: '#9a9b35',
      600: '#787928',
      700: '#55571c',
      800: '#33340f',
      900: '#121203',
    },
  },
  fonts: {
    heading: '"Inter", sans-serif',
    body: '"Inter", sans-serif',
  },
  styles: {
    global: {
      body: {
        bg: 'gray.50',
      },
    },
  },
  components: {
    // Custom component styles
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'lg',
          boxShadow: 'md',
        },
      },
    },
  },
});

export default theme;
