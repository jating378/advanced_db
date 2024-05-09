const express = require('express');
const path = require('path');
const mongoose = require('mongoose');

const app = express();

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/weather_db', { useNewUrlParser: true, useUnifiedTopology: true });
const db = mongoose.connection;

//schema for weather data
const weatherSchema = new mongoose.Schema({
    city: String,
    data: Object,
});

const Weather = mongoose.model('Weather', weatherSchema);

//route to fetch and store weather data for multiple cities
app.get('/fetch-weather', async (req, res) => {
    try {
        // List of cities
        const cities = ['Berlin', 'Mannheim', 'Hamburg', 'Munich', 'Heidelberg'];

        // Dynamic import of node-fetch
        const { default: fetch } = await import('node-fetch');

        // Fetch weather data for each city
        for (const city of cities) {
            const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=fb86a18b6985abcbf3d889795255ea6b&units=metric`);
            const data = await response.json();

            // Store weather data in MongoDB
            const weather = new Weather({
                city: city,
                data: data,
            });
            await weather.save();
        }

        res.status(200).send('Weather data fetched and stored successfully');
    } catch (error) {
        console.error('Error fetching and storing weather data:', error);
        res.status(500).send('An error occurred while fetching and storing weather data');
    }
});

//route to handle requests to the root URL
app.get('/', (req, res) => {
    res.send('Hello, World!'); // Send a simple response
});

// Start the server
const port = 3005;
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
