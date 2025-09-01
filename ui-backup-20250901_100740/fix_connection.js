// Manual connection test - paste this in browser console
async function testConnection() {
    console.log('Testing connection to backend...');
    
    try {
        const response = await fetch('http://localhost:7777/healthz', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ SUCCESS:', data);
            return data;
        } else {
            console.error('❌ HTTP Error:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('❌ Connection Error:', error.message);
    }
}

// Run test
testConnection();
