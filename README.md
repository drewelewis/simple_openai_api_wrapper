# Azure FastAPI Wrapper over Azure OpenAI

A FastAPI-based wrapper service for Azure OpenAI with health monitoring, designed to run on Azure Container Apps with API Management load balancing.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Azure API Management Setup](#azure-api-management-setup)
- [APIM Policy Details](#apim-policy-details)
- [Health Check & Circuit Breaker](#health-check--circuit-breaker)
- [Monitoring & Debugging](#monitoring--debugging)
- [Production Deployment](#production-deployment)

## Features

✅ FastAPI wrapper for Azure OpenAI completion and chat endpoints  
✅ Health check endpoint with Azure OpenAI connectivity verification  
✅ Returns proper HTTP status codes (200, 401, 429, 503)  
✅ Ready for Azure Container Apps deployment  
✅ APIM policies for load balancing with session affinity  
✅ Circuit breaker pattern for automatic failover  
✅ Automatic backend recovery on health restoration  

## Getting Started

### Local Development

1. **Create virtual environment**
   ```bash
   _env_create.bat
   ```

2. **Activate virtual environment**
   ```bash
   _env_activate.bat
   ```

3. **Install dependencies**
   ```bash
   _install.bat
   ```

4. **Configure environment variables**
   - Copy `env.sample` to `.env`
   - Fill in your Azure OpenAI credentials:
     ```env
     OPENAI_ENDPOINT="https://your-instance.openai.azure.com/"
     OPENAI_API_KEY="your-api-key"
     OPENAI_API_VERSION="2025-01-01-preview"
     OPENAI_MODEL_DEPLOYMENT_NAME="gpt-4"
     OPENAI_PROMPT="You are a helpful assistant."
     ```

5. **Start the server**
   ```bash
   _run_server.bat
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /health
Health check endpoint that verifies Azure OpenAI connectivity.

**Response Codes:**
- `200` - Service healthy, Azure OpenAI connected
- `401` - Azure OpenAI authentication failed
- `429` - Azure OpenAI rate limit exceeded
- `503` - Azure OpenAI service unavailable or connection error
- `500` - Unexpected error

**Example:**
```bash
curl http://localhost:8000/health
```

**Success Response:**
```json
{
  "status": "ok",
  "azure_openai": "connected"
}
```

**Error Response (503):**
```json
{
  "status": "error",
  "error": "service_unavailable",
  "message": "Azure OpenAI service unavailable",
  "details": "..."
}
```

### GET /completion
Simple completion endpoint with a single query parameter.

**Parameters:**
- `query` (string, optional) - Default: "how are you?"

**Example:**
```bash
curl "http://localhost:8000/completion?query=Tell me a joke"
```

### POST /chat
Chat endpoint supporting message history.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is Azure?"}
    ]
  }'
```

---

## Azure API Management Setup

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      [INTERNET]                              │
│                       Clients                                │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              [AZURE API MANAGEMENT]                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        Load Balancer + Circuit Breaker              │    │
│  │  • Session Affinity (Sticky Sessions)               │    │
│  │  • Health-Based Routing                             │    │
│  │  • Auto Failover & Recovery                         │    │
│  └─────────────────┬────────────────────────────────────┘    │
└────────────────────┼──────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ... (5 instances)
│ ✅ HEALTHY  │ │ ❌ UNHEALTHY│
│ Container   │ │ Container   │
│ App #1      │ │ App #2      │
│ [ACTIVE]    │ │ [REMOVED]   │
└─────────────┘ └─────────────┘

Legend:
  ✅ [HEALTHY]   - Backend available in pool, receiving traffic
  ❌ [UNHEALTHY] - Backend removed from pool, no traffic
  ⏱️ [UNKNOWN]   - Backend status being evaluated
```

### Load Balancing Features

1. **Session Affinity (Sticky Sessions)** - Clients stick to the same backend via cookies
2. **Circuit Breaker** - Unhealthy backends automatically removed from pool
3. **Auto-Recovery** - Backends rejoin when returning 200 OK
4. **Health-Aware Routing** - Only route to healthy instances

---

## APIM Policy Details

### Main Policy (apim-policy.xml)

This policy provides intelligent load balancing across 5 Azure Container App instances.

```xml
<!--
    Azure API Management Policy for Load Balancing with Session Affinity and Circuit Breaker
    
    Features:
    - Cookie-based session affinity (sticky sessions)
    - Automatic circuit breaking based on backend health
    - Failover to healthy instances when backend returns 500, 429, or 401
    - Automatic recovery when backends return 200 OK
    
    Apply this policy at the API level for your main endpoints
-->
<policies>
    <inbound>
        <base />
        
        <!-- Check for healthy backends from cache -->
        <set-variable name="healthyBackends" value="@{
            var allBackends = new[] { "0", "1", "2", "3", "4" };
            var healthyList = new System.Collections.Generic.List<string>();
            
            foreach (var id in allBackends)
            {
                string cacheKey = "backend-health-" + id;
                string healthStatus;
                
                if (context.Cache.TryGetValue(cacheKey, out healthStatus))
                {
                    if (healthStatus == "healthy")
                    {
                        healthyList.Add(id);
                    }
                }
                else
                {
                    healthyList.Add(id);
                }
            }
            
            return healthyList.Count > 0 ? healthyList.ToArray() : allBackends;
        }" />
        
        <!-- Session affinity with health check -->
        <choose>
            <when condition="@(context.Request.Headers.GetValueOrDefault("Cookie","").Contains("APIM-Backend-Instance"))">
                <set-variable name="backendInstance" value="@{
                    string cookie = context.Request.Headers.GetValueOrDefault("Cookie","");
                    var match = System.Text.RegularExpressions.Regex.Match(cookie, @"APIM-Backend-Instance=(\d+)");
                    string requestedId = match.Success ? match.Groups[1].Value : null;
                    var healthyBackends = (string[])context.Variables["healthyBackends"];
                    
                    if (requestedId != null && healthyBackends.Contains(requestedId))
                    {
                        return requestedId;
                    }
                    
                    var random = new Random();
                    return healthyBackends[random.Next(0, healthyBackends.Length)];
                }" />
            </when>
            <otherwise>
                <set-variable name="backendInstance" value="@{
                    var healthyBackends = (string[])context.Variables["healthyBackends"];
                    var random = new Random();
                    return healthyBackends[random.Next(0, healthyBackends.Length)];
                }" />
            </otherwise>
        </choose>
        
        <!-- Set backend URL based on instance ID -->
        <set-backend-service base-url="@{
            string id = context.Variables.GetValueOrDefault<string>("backendInstance", "0");
            var backends = new System.Collections.Generic.Dictionary<string, string> {
                { "0", "https://your-app-instance-1.azurecontainerapps.io" },
                { "1", "https://your-app-instance-2.azurecontainerapps.io" },
                { "2", "https://your-app-instance-3.azurecontainerapps.io" },
                { "3", "https://your-app-instance-4.azurecontainerapps.io" },
                { "4", "https://your-app-instance-5.azurecontainerapps.io" }
            };
            return backends.ContainsKey(id) ? backends[id] : backends["0"];
        }" />
        
        <set-header name="X-APIM-Correlation-Id" exists-action="skip">
            <value>@(Guid.NewGuid().ToString())</value>
        </set-header>
        
        <set-header name="X-Backend-Instance" exists-action="override">
            <value>@(context.Variables.GetValueOrDefault<string>("backendInstance", "0"))</value>
        </set-header>
    </inbound>
    
    <backend>
        <base />
    </backend>
    
    <outbound>
        <base />
        
        <!-- Circuit breaker: Update health status based on response -->
        <choose>
            <when condition="@(context.Response.StatusCode >= 500 || context.Response.StatusCode == 429 || context.Response.StatusCode == 401)">
                <!-- Mark backend as unhealthy for 30 seconds on errors -->
                <cache-store-value key="@("backend-health-" + context.Variables.GetValueOrDefault<string>("backendInstance"))" value="unhealthy" duration="30" />
            </when>
            <when condition="@(context.Response.StatusCode == 200)">
                <!-- Mark backend as healthy on 200 OK response -->
                <cache-store-value key="@("backend-health-" + context.Variables.GetValueOrDefault<string>("backendInstance"))" value="healthy" duration="30" />
            </when>
        </choose>
        
        <!-- Set session affinity cookie -->
        <set-header name="Set-Cookie" exists-action="append">
            <value>@{
                string instance = context.Variables.GetValueOrDefault<string>("backendInstance", "0");
                return $"APIM-Backend-Instance={instance}; Path=/; Max-Age=86400; HttpOnly; Secure; SameSite=Lax";
            }</value>
        </set-header>
        
        <set-header name="X-Served-By-Instance" exists-action="override">
            <value>@(context.Variables.GetValueOrDefault<string>("backendInstance", "0"))</value>
        </set-header>
    </outbound>
    
    <on-error>
        <base />
        
        <!-- Circuit breaker: Mark backend as unhealthy on connection errors -->
        <cache-store-value key="@("backend-health-" + context.Variables.GetValueOrDefault<string>("backendInstance", "0"))" value="unhealthy" duration="30" />
        
        <set-header name="X-Error-Backend-Instance" exists-action="override">
            <value>@(context.Variables.GetValueOrDefault<string>("backendInstance", "unknown"))</value>
        </set-header>
    </on-error>
</policies>
```

### Setup Steps

1. **Update Backend URLs**
   
   In the policy XML, replace the placeholder URLs:
   ```csharp
   var backends = new System.Collections.Generic.Dictionary<string, string> {
       { "0", "https://your-app-instance-1.azurecontainerapps.io" },
       { "1", "https://your-app-instance-2.azurecontainerapps.io" },
       { "2", "https://your-app-instance-3.azurecontainerapps.io" },
       { "3", "https://your-app-instance-4.azurecontainerapps.io" },
       { "4", "https://your-app-instance-5.azurecontainerapps.io" }
   };
   ```

2. **Apply Policy in Azure Portal**
   - Navigate to your APIM service
   - Go to your API → Design tab
   - Click "All operations" (or specific operations)
   - In "Inbound processing", click the code editor (`</>`)
   - Paste the policy XML
   - Click Save

3. **Deploy Container Apps**
   - Deploy 5 instances of this application to Azure Container Apps
   - Ensure each has a unique URL
   - Verify `/health` endpoint is accessible

---

## Health Check & Circuit Breaker

### How It Works

#### ❌ UNHEALTHY - Marking Backends Unhealthy

A backend is marked **[UNHEALTHY]** (removed from pool for 30 seconds) when:
- Returns `500`, `502`, `503`, `504` (Server errors)
- Returns `429` (Rate limit exceeded)
- Returns `401` (Authentication failed)
- Connection timeout or failure

#### ✅ HEALTHY - Automatic Recovery

A backend is marked **[HEALTHY]** (rejoins pool) when:
- Returns `200 OK`
- Health status cache expires (after 30 seconds)

### Health Status Flow

```
┌─────────────────────────┐
│   [START] Request       │
│   Incoming              │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ [CHECK] Read Cache      │
│ Get Healthy Backends    │
│ (Instances 0-4)         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ [DECISION] Does client  │
│ have session cookie?    │
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │           │
   [YES]        [NO]
      │           │
      ▼           ▼
┌─────────────┐  ┌──────────────────┐
│[CHECK] Is   │  │[ASSIGN] Pick     │
│cookie's     │  │random healthy    │
│backend      │  │backend (0-4)     │
│healthy?     │  └────────┬─────────┘
└──────┬──────┘           │
       │                  │
   ┌───┴───┐              │
   │       │              │
 [YES]   [NO]             │
   │       │              │
   │       └──────┬───────┘
   │              │
   │              ▼
   │       ┌──────────────────┐
   │       │[REASSIGN] Pick   │
   │       │different healthy │
   │       │backend           │
   │       └─────────┬────────┘
   │                 │
   └────────┬────────┘
            │
            ▼
┌─────────────────────────┐
│ [ROUTE] Forward to      │
│ Selected Backend        │
│ Instance (0-4)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ [RESPONSE] Backend      │
│ Returns Status Code     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ [EVALUATE] Check Status │
│ Code from Backend       │
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │           │
 [200 OK]   [ERROR: 401/429/500+]
      │           │
      ▼           ▼
┌─────────────┐  ┌──────────────────┐
│✅ HEALTHY   │  │❌ UNHEALTHY       │
│Cache as     │  │Cache as          │
│"healthy"    │  │"unhealthy"       │
│TTL: 30s     │  │TTL: 30s          │
│[AVAILABLE]  │  │[REMOVED FROM     │
│             │  │ POOL]            │
└─────────────┘  └──────────────────┘
```

### Behavior Table

| Backend Response | Circuit Breaker Action | Status Symbol | Duration | Client Impact |
|-----------------|------------------------|---------------|----------|---------------|
| `200 OK` | Mark healthy | ✅ [HEALTHY] | 30s cache | Continues routing |
| `401 Unauthorized` | Mark unhealthy, remove from pool | ❌ [UNHEALTHY] | 30s | Route to different backend |
| `429 Rate Limit` | Mark unhealthy, remove from pool | ❌ [UNHEALTHY] | 30s | Route to different backend |
| `500+ Server Error` | Mark unhealthy, remove from pool | ❌ [UNHEALTHY] | 30s | Route to different backend |
| Connection Error | Mark unhealthy, remove from pool | ❌ [UNHEALTHY] | 30s | Route to different backend |
| Cache Expired | Re-evaluate on next request | ⏱️ [UNKNOWN] | N/A | May retry backend |

---

## Monitoring & Debugging

### Response Headers

The APIM policy adds several headers for monitoring:

#### Request Headers (Added by APIM)
- **`X-APIM-Correlation-Id`**: Unique request ID for tracing
- **`X-Backend-Instance`**: Which backend (0-4) will handle the request

#### Response Headers
- **`X-Served-By-Instance`**: Which backend actually served the response
- **`X-Error-Backend-Instance`**: (On errors) Which backend caused the error

#### Cookies
- **`APIM-Backend-Instance`**: Session affinity cookie (value 0-4, 24hr TTL)

### Testing Session Affinity

```bash
# First request - receives a backend assignment
curl -i https://your-apim.azure-api.net/completion

# Check the Set-Cookie header for: APIM-Backend-Instance=X

# Subsequent requests with cookie go to same backend
curl -i https://your-apim.azure-api.net/completion \
  -H "Cookie: APIM-Backend-Instance=0"
```

### Testing Circuit Breaker

1. **Simulate Failure**
   ```bash
   # Stop one Container App instance or cause it to return 500s
   ```

2. **Observe Failover**
   ```bash
   # Requests automatically route to healthy instances
   curl -i https://your-apim.azure-api.net/health | grep X-Served-By-Instance
   ```

3. **Test Recovery**
   ```bash
   # Restart the instance, wait 30 seconds
   # It automatically rejoins the pool on first 200 response
   ```

### Monitor Backend Health

Check which backends are currently healthy:
```bash
# Make requests and check which instances respond
for i in {1..10}; do
  curl -s https://your-apim.azure-api.net/completion \
    -i | grep "X-Served-By-Instance"
done
```

---

## Production Deployment

### Prerequisites

- Azure subscription
- Azure API Management instance
- 5 Azure Container App instances
- Container registry (Azure Container Registry recommended)

### Container App Deployment

1. **Build Docker image**
   ```bash
   docker build -t your-registry.azurecr.io/openai-wrapper:latest .
   ```

2. **Push to registry**
   ```bash
   docker push your-registry.azurecr.io/openai-wrapper:latest
   ```

3. **Deploy to Container Apps**
   ```bash
   az containerapp create \
     --name openai-wrapper-1 \
     --resource-group your-rg \
     --environment your-env \
     --image your-registry.azurecr.io/openai-wrapper:latest \
     --target-port 8000 \
     --ingress external \
     --env-vars \
       OPENAI_ENDPOINT="https://your-instance.openai.azure.com/" \
       OPENAI_API_KEY="your-key" \
       OPENAI_API_VERSION="2025-01-01-preview" \
       OPENAI_MODEL_DEPLOYMENT_NAME="gpt-4"
   ```

   Repeat for instances 2-5 with different names.

### APIM Configuration

1. **Enable Internal Cache** (Required for circuit breaker)
   - Navigate to APIM → Caching
   - Enable built-in cache

2. **Import API**
   - Create or import your OpenAI wrapper API
   - Add operations: `/health`, `/completion`, `/chat`

3. **Apply Policy**
   - Use the policy XML from `apim-policy.xml`
   - Update backend URLs
   - Apply at API level or operation level

### Production Checklist

- [ ] Internal cache enabled in APIM
- [ ] All 5 Container Apps deployed and running
- [ ] Health endpoints returning 200 OK
- [ ] Backend URLs updated in APIM policy
- [ ] Policy applied and tested
- [ ] Session affinity tested with cookies
- [ ] Circuit breaker tested with simulated failures
- [ ] Monitoring/alerts configured (Application Insights)
- [ ] Security: APIM subscription keys configured
- [ ] Security: Container Apps ingress restricted to APIM (if needed)

### Production Considerations

1. **Cache TTL**: 30 seconds is default, adjust based on recovery time needs
2. **Monitoring**: Set up Application Insights for both APIM and Container Apps
3. **Alerts**: Create alerts when >50% of backends are unhealthy
4. **Scaling**: Configure Container Apps autoscaling based on CPU/memory
5. **Security**: Use Azure Key Vault for storing OpenAI API keys
6. **Rate Limits**: Configure APIM rate limiting policies
7. **Quotas**: Set appropriate quotas per client/subscription

### Troubleshooting

**Issue**: All requests go to same instance
- **Fix**: Verify APIM cache is enabled
- **Fix**: Check `Set-Cookie` header is being sent
- **Fix**: Test without cookies to verify random distribution

**Issue**: Backends not marked unhealthy on failures
- **Fix**: Verify `/health` endpoint returns correct status codes
- **Fix**: Check APIM diagnostic logs
- **Fix**: Ensure cache is properly configured

**Issue**: Circuit breaker not recovering
- **Fix**: Wait 30 seconds for cache expiration
- **Fix**: Ensure backend returns `200 OK`
- **Fix**: Check `X-Served-By-Instance` header

**Issue**: High latency on health checks
- **Fix**: Health checks are passive (based on regular traffic)
- **Fix**: Consider implementing active health monitoring

---

## Project Structure

```
simple_openai_api_wrapper/
├── ai/
│   └── azure_openai_client.py    # Azure OpenAI client wrapper
├── app/
│   ├── __init__.py
│   ├── chat_completion.py        # Completion and chat logic
│   └── main.py                   # FastAPI application and endpoints
├── models/
│   └── model.py                  # Pydantic models
├── apim-policy.xml               # Main APIM policy (load balancing + circuit breaker)
├── apim-healthcheck-monitor.xml  # Optional active health monitoring policy
├── docker-compose.yaml           # Local development with Docker
├── dockerfile                    # Container image definition
├── env.sample                    # Environment variable template
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://your-instance.openai.azure.com/` |
| `OPENAI_API_KEY` | Azure OpenAI API key | `your-api-key` |
| `OPENAI_API_VERSION` | API version | `2025-01-01-preview` |
| `OPENAI_MODEL_DEPLOYMENT_NAME` | Deployment name | `gpt-4` or `o1` |
| `OPENAI_PROMPT` | Default system prompt | `You are a helpful assistant.` |

## License

MIT

