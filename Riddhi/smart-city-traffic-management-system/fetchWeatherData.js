    import axios from 'axios';
    import fs from 'fs';

    const apiKey = 'fb86a18b6985abcbf3d889795255ea6b';
    
    const cities = ['Heidelberg', 'Berlin', 'Munich', 'Hamburg',];

    const fetchWeatherData = async (city) => {
    try {
        // Fetch weather data from OpenWeatherMap API
        const response = await axios.get(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching weather data for ${city}:`, error.message);
        return null;
    }
    };

    // Function to fetch weather data for all cities
    const fetchAllWeatherData = async () => {
    const weatherData = {};
    for (const city of cities) {
        const data = await fetchWeatherData(city);
        if (data) {
        weatherData[city] = data;
        }
    }
    return weatherData;
    };

    // Fetching weather data for all cities
    fetchAllWeatherData()
    .then((weatherData) => {
        fs.writeFileSync('weatherData.json', JSON.stringify(weatherData, null, 2));
        console.log('Weather data has been fetched and saved to weatherData.json');
    })
    .catch((error) => {
        console.error('An error occurred while fetching weather data:', error.message);
    });
