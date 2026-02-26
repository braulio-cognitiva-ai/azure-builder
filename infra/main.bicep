// Main infrastructure template for Azure Builder
targetScope = 'resourceGroup'

@description('Environment name (dev, staging, production)')
param environment string = 'production'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Application name')
param appName string = 'azurebuilder'

// Variables
var uniqueSuffix = uniqueString(resourceGroup().id)
var containerAppEnvName = '${appName}-env-${environment}'
var keyVaultName = 'kv-${appName}-${uniqueSuffix}'
var postgresName = 'psql-${appName}-${environment}'
var redisName = 'redis-${appName}-${environment}'
var serviceBusName = 'sb-${appName}-${environment}'

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    daprAIInstrumentationKey: ''
    appLogsConfiguration: {
      destination: 'log-analytics'
    }
  }
}

// Azure Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// PostgreSQL Flexible Server
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: postgresName
  location: location
  sku: {
    name: 'Standard_B2s'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: 'azureadmin'
    administratorLoginPassword: keyVault.getSecret('postgres-admin-password')
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
  }
}

// Redis Cache
resource redis 'Microsoft.Cache/redis@2023-04-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// Service Bus Namespace
resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

// Service Bus Queue for executions
resource executionQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBus
  name: 'execution-jobs'
  properties: {
    maxDeliveryCount: 3
    lockDuration: 'PT5M'
    requiresDuplicateDetection: false
  }
}

// Backend Container App
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-backend-${environment}'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: [
        {
          name: 'database-url'
          value: 'postgresql+asyncpg://azureadmin:${keyVault.getSecret('postgres-admin-password')}@${postgres.properties.fullyQualifiedDomainName}:5432/azurebuilder'
        }
        {
          name: 'redis-url'
          value: 'redis://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:6380'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'azurebuilder/backend:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

// Outputs
output backendUrl string = backendApp.properties.configuration.ingress.fqdn
output keyVaultName string = keyVault.name
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output redisHost string = redis.properties.hostName
