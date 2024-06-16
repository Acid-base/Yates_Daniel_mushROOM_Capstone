// frontend/src/api.ts

import { Mushroom } from "./types";

const MAX_RETRIES = 5;
const INITIAL_DELAY_MS = 5000;
const RATE_LIMIT_MS = 5000;

const handleRateLimit = async (
  apiUrl: string,
  retryCount: number,
  delay: number,
): Promise<{ retryCount: number; delay: number }> => {
  if (retryCount >= MAX_RETRIES) {
    throw new Error(`Rate limit exceeded maximum retries for ${apiUrl}`);
  }
  console.warn(
    `Rate limit exceeded (attempt ${retryCount + 1}). Retrying in ${delay / 1000} seconds...`,
  );
  await new Promise((resolve) => setTimeout(resolve, delay));
  return { retryCount: retryCount + 1, delay: delay * 2 };
};

export const fetchMushrooms = async (
  searchTerm: string = "",
  pageNumber: number = 1,
): Promise<Mushroom[]> => {
  try {
    const response = await fetch(
      `https://your-api-base-url.com/mushrooms?q=${searchTerm}&page=${pageNumber}&size=20`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data: Mushroom[] = await response.json(); // Specify data type
    return data;
  } catch (error) {
    console.error("Error fetching data:", error);
    throw error;
  }
};

export const fetchMushroomDetails = async (
  mushroomId: string | number,
): Promise<Mushroom> => {
  try {
    const apiUrl = `/api/mushrooms/${mushroomId}`;
    let retryCount = 0;
    let delay = INITIAL_DELAY_MS;

    while (retryCount <= MAX_RETRIES) {
      const response = await fetch(apiUrl);

      if (!response.ok) {
        if (response.status === 429) {
          ({ retryCount, delay } = await handleRateLimit(
            apiUrl,
            retryCount,
            delay,
          ));
        } else {
          throw new Error(`API request failed with status: ${response.status}`);
        }
      } else {
        const data: Mushroom = await response.json();
        return data;
      }
    }

    throw new Error(`Max retries exceeded for ${apiUrl}`);
  } catch (error) {
    console.error("Error fetching mushroom details:", error);
    throw error;
  }
};
