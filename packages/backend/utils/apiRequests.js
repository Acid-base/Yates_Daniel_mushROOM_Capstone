import fetch from 'node-fetch';
import { URL } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const MUSHROOM_OBSERVER_API_KEY = process.env.MUSHROOM_OBSERVER_API_KEY;

const fetchMushroomData = async (endpoint, params = {}) => {
  try {
    const url = new URL(`https://mushroomobserver.org/api2/${endpoint}`);
    Object.entries(params).forEach(([key, value]) => url.searchParams.append(key, value));

    const response = await fetch(url.toString(), {
      headers: {
        'Authorization': `Bearer ${MUSHROOM_OBSERVER_API_KEY}`,
        'X-RateLimit-Limit': '15', // Set the rate limit (adjust as needed)
        'X-RateLimit-Window': '60', // Set the rate limit window (in seconds)
      },
    });

    console.log(`Fetching data from ${url.toString()}`);

    if (!response.ok) {
      const errorData = await response.json();
      console.error("API Error:", errorData);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || "Unknown error"}`);
    }

    const data = await response.json();
    console.log("API Response:", data);
    return data;
  } catch (error) {
    console.error(`Error fetching data from Mushroom Observer API: ${error.message}`);
    throw error;
  }
};

export default fetchMushroomData;
