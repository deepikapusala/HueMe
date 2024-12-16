// Use `import` instead of `require`
import got from 'got'; // ESM-compatible HTTP request library
import fs from 'fs';
import FormData from 'form-data';

// Replace with your Imagga API credentials
const apiKey = 'acc_29e582455d9c5c3';
const apiSecret = 'db8920d6ef407ded0f8362a1d39d106c';

// Replace with the path to your image file
const filePath = 'Spring.jpeg';

const formData = new FormData();
formData.append('image', fs.createReadStream(filePath));
formData.append('resolution', '100x100,500x300'); // Specify resolution if needed

(async () => {
    try {
        const response = await got.post('https://api.imagga.com/v2/colors', {
            body: formData,
            username: apiKey,
            password: apiSecret,
        });
        console.log('Image Analysis Result:');
        console.log(JSON.parse(response.body));
    } catch (error) {
        console.error('Error:', error.response?.body || error.message);
    }
})();