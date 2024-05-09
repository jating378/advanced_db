import axios from 'axios';
import fs from 'fs';

// Array of cities
const cities = ['Heidelberg', 'Berlin', 'Munich'];

// Function to fetch air quality data for a city
const fetchAirQualityData = async (city) => {
    try {
        // Fetch air quality data from OpenAQ API
        const response = await axios.get(`https://api.openaq.org/v1/latest?city=${city}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching air quality data for ${city}:`, error.message);
        return null;
    }
};

// Function to fetch air quality data for all cities
const fetchAllAirQualityData = async () => {
    const airQualityData = {};
    for (const city of cities) {
        const data = await fetchAirQualityData(city);
        if (data) {
            airQualityData[city] = data;
        }
    }
    return airQualityData;
};

// Fetch air quality data for all cities
fetchAllAirQualityData()
    .then((airQualityData) => {
        // Writes air quality data to JSON file
        fs.writeFileSync('airQualityData.json', JSON.stringify(airQualityData, null, 2));
        console.log('Air quality data has been fetched and saved to airQualityData.json');
    })
    .catch((error) => {
        console.error('An error occurred while fetching air quality data:', error.message);
    });
