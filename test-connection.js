const axios = require('axios');

const BACKEND_URL = 'http://localhost:8888';

async function testBackendConnection() {
  console.log('Testing backend connection...');
  
  try {
    // Test health endpoint first
    console.log('1. Testing health endpoint...');
    const healthResponse = await axios.get(`${BACKEND_URL}/health`);
    console.log('✅ Health check passed:', healthResponse.data);
    
    // Test command endpoint
    console.log('2. Testing command endpoint...');
    const commandResponse = await axios.post(`${BACKEND_URL}/command`, {
      command: 'test',
      context: []
    }, {
      timeout: 30000
    });
    
    console.log('✅ Command test passed:', commandResponse.data);
    
  } catch (error) {
    console.error('❌ Connection failed:', {
      code: error.code,
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : 'No response'
    });
  }
}

testBackendConnection();
