#!/usr/bin/env node

const axios = require('axios');

const BACKEND_URL = 'http://localhost:8888';

async function testBackend() {
    console.log('🧪 Testing Cluely Backend Connection');
    console.log('====================================');
    
    try {
        console.log('\n1. Testing health endpoint...');
        const health = await axios.get(`${BACKEND_URL}/health`);
        console.log('✅ Health check passed:', health.data);
        
        console.log('\n2. Testing AI command...');
        const aiCommand = await axios.post(`${BACKEND_URL}/command`, {
            command: 'Hello, can you help me?',
            context: []
        });
        
        console.log('✅ AI Command result:');
        console.log('   Success:', aiCommand.data.success);
        console.log('   Is AI Response:', aiCommand.data.is_ai_response);
        console.log('   Method:', aiCommand.data.metadata?.method);
        console.log('   Result length:', aiCommand.data.result?.length);
        console.log('   Result preview:', aiCommand.data.result?.substring(0, 100) + '...');
        
        console.log('\n3. Testing file command...');
        const fileCommand = await axios.post(`${BACKEND_URL}/command`, {
            command: 'list files in current directory',
            context: []
        });
        
        console.log('✅ File Command result:');
        console.log('   Success:', fileCommand.data.success);
        console.log('   Is AI Response:', fileCommand.data.is_ai_response);
        console.log('   Method:', fileCommand.data.metadata?.method);
        console.log('   Result preview:', fileCommand.data.result?.substring(0, 100) + '...');
        
        console.log('\n🎉 All tests passed! Backend is working correctly.');
        console.log('\nIf the overlay is not showing responses:');
        console.log('1. Make sure you pressed Cmd+Space to activate the overlay');
        console.log('2. Check the Electron developer console for errors');
        console.log('3. Try asking: "Hello, can you help me?" or "tell me a joke"');
        
    } catch (error) {
        console.error('❌ Backend test failed:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            console.log('\n💡 Backend is not running. Start it with:');
            console.log('   npm run backend');
        }
    }
}

testBackend();
