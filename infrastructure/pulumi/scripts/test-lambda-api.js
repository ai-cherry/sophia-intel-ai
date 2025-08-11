#!/usr/bin/env node

const axios = require('axios');

// Lambda Labs API Configuration
const LAMBDA_API_KEY = process.env.LAMBDA_API_KEY;
const LAMBDA_CLOUD_API_KEY = process.env.LAMBDA_CLOUD_API_KEY;

if (!LAMBDA_API_KEY || !LAMBDA_CLOUD_API_KEY) {
    console.error('❌ Missing Lambda Labs API keys');
    console.error('   LAMBDA_API_KEY:', LAMBDA_API_KEY ? '✅ Set' : '❌ Missing');
    console.error('   LAMBDA_CLOUD_API_KEY:', LAMBDA_CLOUD_API_KEY ? '✅ Set' : '❌ Missing');
    process.exit(1);
}

// API Endpoints
const ENDPOINTS = {
    instances: 'https://cloud.lambda.ai/api/v1/instances',
    instanceTypes: 'https://cloud.lambda.ai/api/v1/instance-types',
    sshKeys: 'https://cloud.lambda.ai/api/v1/ssh-keys',
};

// Test Lambda Labs API connectivity
async function testLambdaAPI() {
    console.log('🧪 Testing Lambda Labs API connectivity...\n');

    // Test with primary API key
    await testEndpoint('Primary API', LAMBDA_API_KEY, ENDPOINTS.instances);
    await testEndpoint('Primary API', LAMBDA_API_KEY, ENDPOINTS.instanceTypes);
    
    // Test with cloud API key
    await testEndpoint('Cloud API', LAMBDA_CLOUD_API_KEY, ENDPOINTS.instances);
    await testEndpoint('Cloud API', LAMBDA_CLOUD_API_KEY, ENDPOINTS.instanceTypes);
    
    console.log('\n✅ Lambda Labs API testing completed');
}

async function testEndpoint(apiType, apiKey, endpoint) {
    try {
        console.log(`📡 Testing ${apiType} - ${endpoint}`);
        
        const response = await axios.get(endpoint, {
            auth: {
                username: apiKey,
                password: ''
            },
            timeout: 10000,
        });
        
        console.log(`   ✅ Status: ${response.status}`);
        console.log(`   📊 Response: ${JSON.stringify(response.data).substring(0, 100)}...`);
        
    } catch (error) {
        console.log(`   ❌ Error: ${error.response?.status || error.code}`);
        console.log(`   📝 Message: ${error.response?.data?.error || error.message}`);
    }
    console.log('');
}

// Create Lambda Labs instance
async function createInstance() {
    console.log('🚀 Creating Lambda Labs instance for Sophia Intel...\n');
    
    const instanceConfig = {
        region_name: 'us-east-1',
        instance_type_name: 'gpu_1x_h100_pcie',
        ssh_key_names: ['sophia-intel-key'],
        name: `sophia-intel-${Date.now()}`,
    };
    
    try {
        const response = await axios.post(ENDPOINTS.instances, instanceConfig, {
            auth: {
                username: LAMBDA_API_KEY,
                password: ''
            },
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 30000,
        });
        
        console.log('✅ Instance creation initiated');
        console.log('📋 Instance details:', JSON.stringify(response.data, null, 2));
        
        return response.data;
        
    } catch (error) {
        console.log('❌ Instance creation failed');
        console.log('📝 Error:', error.response?.data || error.message);
        return null;
    }
}

// List available instance types
async function listInstanceTypes() {
    console.log('📋 Listing available Lambda Labs instance types...\n');
    
    try {
        const response = await axios.get(ENDPOINTS.instanceTypes, {
            auth: {
                username: LAMBDA_API_KEY,
                password: ''
            },
            timeout: 10000,
        });
        
        console.log('✅ Available instance types:');
        
        if (response.data && response.data.data) {
            response.data.data.forEach(type => {
                console.log(`   🖥️  ${type.name}`);
                console.log(`      💰 Price: $${type.price_cents_per_hour / 100}/hour`);
                console.log(`      🔧 Specs: ${type.description || 'N/A'}`);
                console.log('');
            });
        }
        
    } catch (error) {
        console.log('❌ Failed to list instance types');
        console.log('📝 Error:', error.response?.data || error.message);
    }
}

// Main execution
async function main() {
    console.log('🧠 Sophia Intel - Lambda Labs API Test\n');
    console.log('=' * 50);
    
    // Test API connectivity
    await testLambdaAPI();
    
    // List available instance types
    await listInstanceTypes();
    
    // Optionally create instance (commented out for safety)
    // await createInstance();
    
    console.log('🎉 Lambda Labs integration test completed!');
}

// Run the test
if (require.main === module) {
    main().catch(error => {
        console.error('💥 Test failed:', error.message);
        process.exit(1);
    });
}

module.exports = {
    testLambdaAPI,
    createInstance,
    listInstanceTypes,
};

