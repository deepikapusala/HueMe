const express = require('express');
const multer = require('multer');
const bodyParser = require('body-parser');
const path = require('path');
const vision = require('@google-cloud/vision');

const app = express();
const PORT = 3000;

// Configure Multer for file uploads
const storage = multer.diskStorage({
    destination: './uploads',
    filename: (req, file, cb) => {
        cb(null, file.originalname);
    },
});
const upload = multer({ storage });

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));
app.set('view engine', 'ejs');

// Google Cloud Vision client
const client = new vision.ImageAnnotatorClient();

// Routes
app.get('/', (req, res) => {
    res.render('index'); // Ensure an `index.ejs` file exists in the `views` folder
});

app.post('/upload', upload.single('image'), async (req, res) => {
    const imagePath = path.join(__dirname, 'uploads', req.file.filename);

    try {
        // Perform property detection using Google Cloud Vision API
        const [result] = await client.imageProperties(imagePath);
        const colors = result.imagePropertiesAnnotation.dominantColors.colors;

        // Extract colors and determine season
        const dominantColors = colors.map(color => ({
            color: color.color,
            score: color.score,
            pixelFraction: color.pixelFraction,
        }));
        const colorBracket = determineColorBracket(dominantColors);

        res.render('result', { colors: dominantColors, season: colorBracket }); // Ensure a `result.ejs` file exists
    } catch (error) {
        console.error('Error detecting image properties:', error);
        res.status(500).send('Error processing the image');
    }
});

// Function to determine the color bracket
function determineColorBracket(colors) {
    const springColors = ['#FFB6C1', '#FFD700', '#98FB98'];
    const summerColors = ['#87CEEB', '#FF4500', '#32CD32'];
    const autumnColors = ['#D2691E', '#FF8C00', '#8B4513'];
    const winterColors = ['#4682B4', '#708090', '#D3D3D3'];

    let matches = { spring: 0, summer: 0, autumn: 0, winter: 0 };

    colors.forEach(color => {
        const hexColor = rgbToHex(color.color.red, color.color.green, color.color.blue);
        if (springColors.includes(hexColor)) matches.spring++;
        if (summerColors.includes(hexColor)) matches.summer++;
        if (autumnColors.includes(hexColor)) matches.autumn++;
        if (winterColors.includes(hexColor)) matches.winter++;
    });

    const sortedMatches = Object.entries(matches).sort((a, b) => b[1] - a[1]);
    return sortedMatches[0][0]; // Return the season with the highest match
}

// Helper function to convert RGB to HEX
function rgbToHex(r, g, b) {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase()}`;
}

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

