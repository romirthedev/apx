const axios = require('axios');

// This is a simple test script to test the task planner functionality
// It sends a command to the backend API and prints the response

const backendPort = 8889; // Using the alternate port we started on
const backendUrl = `http://localhost:${backendPort}`;

// Test a complex command that should trigger the task planner
async function testTaskPlanner() {
  try {
    // Using a more complex multi-step command
    const command = "find all text files in my Desktop folder and create a new file called summary.txt with their names and sizes";
    console.log(`Testing task planner with command: "${command}"`);
    
    const response = await axios.post(`${backendUrl}/command`, {
      command,
      context: []
    });
    
    console.log("Response:");
    console.log(JSON.stringify(response.data, null, 2));
    
    // Check if the task planner was used
    const metadata = response.data.metadata || {};
    console.log(`Method used: ${metadata.method || 'unknown'}`);
    console.log(`Is AI response: ${response.data.is_ai_response ? 'Yes' : 'No'}`);
    
    // If actions were performed, list them
    if (metadata.actions_performed && metadata.actions_performed.length > 0) {
      console.log("\nActions performed:");
      metadata.actions_performed.forEach((action, i) => {
        console.log(`${i + 1}. Type: ${action.action_type || 'unknown'}`);
        if (action.output) console.log(`   Output: ${action.output}`);
        if (action.error) console.log(`   Error: ${action.error}`);
      });
    }
    
  } catch (error) {
    console.error("Error testing task planner:", error.message);
    if (error.response) {
      console.error("Response data:", error.response.data);
      console.error("Response status:", error.response.status);
    }
  }
}

// Run the test
testTaskPlanner();
