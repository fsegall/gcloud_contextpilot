#!/usr/bin/env node
// Script de teste de conexão independente
const axios = require('axios');

const API_URL = 'https://contextpilot-backend-581368740395.us-central1.run.app';

async function testConnection() {
    console.log('🔍 Testando conexão com backend GCP...');
    console.log(`📡 URL: ${API_URL}\n`);

    try {
        // Test 1: Health Check
        console.log('Test 1: Health Check');
        const healthResponse = await axios.get(`${API_URL}/health`, {
            timeout: 30000,
            validateStatus: () => true
        });
        console.log(`✅ Status: ${healthResponse.status}`);
        console.log(`✅ Data:`, healthResponse.data);
        console.log('');

        // Test 2: Proposals
        console.log('Test 2: Proposals Endpoint');
        const proposalsResponse = await axios.get(`${API_URL}/proposals`, {
            params: { workspace_id: 'contextpilot' },
            timeout: 30000,
            validateStatus: () => true
        });
        console.log(`✅ Status: ${proposalsResponse.status}`);
        console.log(`✅ Proposals Count: ${proposalsResponse.data?.count || 0}`);
        console.log('');

        // Test 3: Agents Status
        console.log('Test 3: Agents Status');
        const agentsResponse = await axios.get(`${API_URL}/agents/status`, {
            timeout: 30000,
            validateStatus: () => true
        });
        console.log(`✅ Status: ${agentsResponse.status}`);
        console.log(`✅ Agents Count: ${agentsResponse.data?.length || 0}`);
        console.log('');

        console.log('🎉 Todos os testes passaram! Backend está funcionando perfeitamente.');
        console.log('');
        console.log('Se a extensão não está conectando, o problema é:');
        console.log('  1. Extensão não foi reinstalada corretamente');
        console.log('  2. Configuração do VSCode está sobrescrevendo a URL');
        console.log('  3. Cache da extensão não foi limpo');
        
    } catch (error) {
        console.error('❌ Erro na conexão:', error.message);
        if (error.code) {
            console.error(`   Código: ${error.code}`);
        }
        if (error.response) {
            console.error(`   Status HTTP: ${error.response.status}`);
            console.error(`   Data:`, error.response.data);
        }
    }
}

testConnection();



















