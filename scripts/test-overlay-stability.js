const axios = require('axios');

async function testOverlayStability() {
  console.log('Testing overlay stability...\n');
  
  const BACKEND_URL = 'http://localhost:8888';
  
  try {
    // Test backend health
    console.log('1. Testing backend health...');
    const healthResponse = await axios.get(`${BACKEND_URL}/health`, {
      family: 4,
      timeout: 5000
    });
    console.log('✅ Backend is healthy\n');
    
    // Test command processing multiple times to check for stability
    console.log('2. Testing command processing stability...');
    const testCommands = [
      'hello',
      'what can you do?',
      'test command',
      'help me',
      'status'
    ];
    
    for (let i = 0; i < testCommands.length; i++) {
      const command = testCommands[i];
      console.log(`   Testing command ${i + 1}/${testCommands.length}: "${command}"`);
      
      try {
        const response = await axios.post(`${BACKEND_URL}/command`, {
          command: command,
          context: []
        }, {
          timeout: 10000,
          family: 4
        });
        
        if (response.data && response.data.success !== false) {
          console.log(`   ✅ Command "${command}" processed successfully`);
        } else {
          console.log(`   ⚠️  Command "${command}" returned error: ${response.data.error || 'Unknown error'}`);
        }
      } catch (error) {
        console.log(`   ❌ Command "${command}" failed: ${error.message}`);
      }
      
      // Small delay between commands
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('\n3. Testing rapid command processing...');
    const rapidCommands = Array(5).fill('quick test');
    const promises = rapidCommands.map((cmd, index) => 
      axios.post(`${BACKEND_URL}/command`, {
        command: `${cmd} ${index + 1}`,
        context: []
      }, {
        timeout: 10000,
        family: 4
      }).then(() => console.log(`   ✅ Rapid command ${index + 1} completed`))
        .catch(err => console.log(`   ❌ Rapid command ${index + 1} failed: ${err.message}`))
    );
    
    await Promise.all(promises);
    
    console.log('\n✅ Overlay stability test completed!');
    console.log('\nTo test the actual overlay UI:');
    console.log('1. Use Cmd+Space (Mac) or Ctrl+Space to open the overlay');
    console.log('2. Type commands and press Enter');
    console.log('3. Check that responses appear and the overlay doesn\'t disappear unexpectedly');
    console.log('4. Check the main Electron app logs for any "Object has been destroyed" errors');
    
  } catch (error) {
    console.error('❌ Backend connectivity test failed:', error.message);
    console.log('\nPlease ensure the backend is running with: npm run backend');
  }
}

testOverlayStability();
