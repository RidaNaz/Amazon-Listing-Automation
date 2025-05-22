// Run this in Node.js to get a new refresh token
const axios = require('axios');

const getRefreshToken = async () => {
  const response = await axios.post('https://api.amazon.com/auth/o2/token', {
    grant_type: 'authorization_code',
    code: 'YOUR_AUTH_CODE', // Get this from Seller Central OAuth flow
    client_id: 'YOUR_CLIENT_ID',
    client_secret: 'YOUR_CLIENT_SECRET',
    redirect_uri: 'https://your-app.com/callback' // Must match app settings
  });
  console.log('New refresh token:', response.data.refresh_token);
  return response.data.refresh_token;
};

getRefreshToken();