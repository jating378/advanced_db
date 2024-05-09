const mongoose = require('mongoose');

const airQualitySchema = new mongoose.Schema({
    _id: mongoose.Schema.Types.ObjectId,
    location: String,
    parameter: String,
    value: Number,
    date: {
        utc: Date,
        local: Date,
        unit: String
    },
    coordinates: {
        latitude: Number,
        longitude: Number
    },
    country: String,
    city: String
});

module.exports = mongoose.model('AirQuality', airQualitySchema);
