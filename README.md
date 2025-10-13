# Simple MCP Server

A simple Model Control Protocol (MCP) server built with FastMCP that provides two useful tools:

1. **Simple Math** - Perform basic arithmetic operations
2. **Weather Lookup** - Get current weather information for any city

## Features

### Math Tool

- Supports: addition, subtraction, multiplication, division
- Handles division by zero errors
- Works with any numeric values (integers or floats)

### Weather Tool

- Real weather data via OpenWeatherMap API (optional)
- Falls back to mock data if no API key provided
- Returns temperature, conditions, and humidity

## Setup

1. **Create a conda environment with Python 3.11:**

   ```bash
   conda create -n mcp-server python=3.11 -y
   conda activate mcp-server
   ```

2. **Install dependencies:**

   ```bash
   pip install fastmcp requests python-dotenv
   ```

3. **Optional - Set up weather API:**

   - Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
   - Set the environment variable:

   ```bash
   export OPENWEATHER_API_KEY=your_api_key_here
   ```

4. **Run the server:**
   ```bash
   python server.py
   ```

The server will start on HTTP transport at `http://0.0.0.0:8000`

## Usage

The MCP server now runs over HTTP transport (Streamable HTTP) which is recommended for web services according to the FastMCP documentation. The server will be accessible at `http://localhost:8000` when running locally.

### Testing with MCP Inspector

You can test your server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### Integration with Claude Desktop

To use this HTTP-based server with Claude Desktop, add it to your MCP configuration file:

**macOS/Linux:** `~/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "simple-mcp-server": {
      "url": "http://localhost:8000/mcp",
      "env": {
        "OPENWEATHER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Integration with MCP Clients

For programmatic access, you can connect to the server using any MCP client:

```python
from fastmcp import Client

# Connect to the HTTP-based MCP server
client = Client("http://localhost:8000/mcp")

# Use the tools
async with client:
    result = await client.call_tool("simple_math", num1=10, num2=5, operation="add")
    print(result)  # "10 add 5 = 15"

    weather = await client.call_tool("get_weather", city="London", country="UK")
    print(weather)
```

### Server Configuration

You can customize the server configuration by modifying the `mcp.run()` call in `server.py`:

```python
mcp.run(
    transport="http",
    host="127.0.0.1",    # Localhost only
    port=9000,           # Custom port
    log_level="DEBUG"    # More verbose logging
)
```

### Tool Examples

**Math Tool:**

- `simple_math(10, 5, "add")` → "10 add 5 = 15"
- `simple_math(20, 4, "divide")` → "20 divide 4 = 5.0"
- `simple_math(7, 3, "multiply")` → "7 multiply 3 = 21"

**Weather Tool:**

- `get_weather("London", "UK")` → "Weather in London, UK: 15°C (feels like 13°C), Partly Cloudy, Humidity: 72%"
- `get_weather("Tokyo", "Japan")` → Current weather information for Tokyo

## Running Multiple MCP Server Instances

If you want to run multiple MCP servers on the same remote server (e.g., `10.100.1.121`), you need to customize several components to avoid conflicts. Here's how to create a second instance:

### Step 1: Check Available Ports

First, check which ports are available on your remote server:

```bash
# SSH to remote server
ssh username@10.100.1.121

# Check if port 8005 is available (should return nothing if free)
sudo netstat -tulpn | grep :8005

# Alternative: check multiple ports at once
sudo netstat -tulpn | grep -E ':(8000|8005|8010|8080)'

# Check if any process is using port 8005
sudo lsof -i :8005
```

### Step 2: Create a Customized Version

Create a new directory for your second MCP server and customize the following files:

#### **1. Update server.py**

Change the server name, port, and tool names:

```python
# Create FastMCP server instance with unique name
mcp = FastMCP("Financial Calculator MCP Server")

@mcp.tool()
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: float,
    compound_frequency: int = 12
) -> str:
    """
    Calculate compound interest for financial planning.

    Args:
        principal: Initial investment amount
        rate: Annual interest rate (as percentage, e.g., 5.5 for 5.5%)
        time: Investment time in years
        compound_frequency: How many times interest compounds per year (default: 12 for monthly)

    Returns:
        String containing the compound interest calculation
    """
    try:
        # Convert percentage to decimal
        rate_decimal = rate / 100

        # Compound interest formula: A = P(1 + r/n)^(nt)
        amount = principal * (1 + rate_decimal/compound_frequency) ** (compound_frequency * time)
        interest = amount - principal

        return f"Principal: ${principal:,.2f}, Rate: {rate}%, Time: {time} years → Final Amount: ${amount:,.2f}, Interest Earned: ${interest:,.2f}"

    except Exception as e:
        return f"Error calculating compound interest: {str(e)}"

@mcp.tool()
def get_stock_info(symbol: str, exchange: str = "NYSE") -> str:
    """
    Get stock information for investment analysis (mock data).

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, GOOGL)
        exchange: Stock exchange (NYSE, NASDAQ, etc.)

    Returns:
        String containing stock information
    """
    # Mock stock data since we don't have a real API
    mock_price = hash(symbol) % 1000 + 50  # Generate consistent mock price
    mock_change = (hash(symbol + exchange) % 20) - 10  # Generate mock change

    return f"Stock Info for {symbol} ({exchange}): Price: ${mock_price:.2f}, Change: {mock_change:+.2f} ({mock_change/mock_price*100:+.1f}%). (Note: This is mock data for demonstration)"

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8005,  # Different port
        log_level="INFO"
    )
```

#### **2. Update docker-compose.yml**

Change the container name, port mapping, and service name:

```yaml
version: '3.8'

services:
  financial-mcp-server: # Different service name
    build:
      context: .
      dockerfile: Dockerfile
    container_name: financial-mcp-server # Different container name
    ports:
      - '8005:8005' # Different port mapping
    environment:
      - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY:-}
    restart: unless-stopped
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8005/'] # Different port
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    labels:
      - 'traefik.enable=true'
      - 'traefik.http.routers.financial-mcp-server.rule=Host(`financial-mcp.yourdomain.com`)'
      - 'traefik.http.services.financial-mcp-server.loadbalancer.server.port=8005'
```

#### **3. Update Dockerfile**

Change the health check port:

```dockerfile
# Update the health check to use the new port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/ || exit 1
```

#### **4. Update deploy.sh**

Change the container name references:

```bash
# In the cleanup() function, update container name
$DOCKER_CMD rm -f financial-mcp-server 2>/dev/null || true

# In check_status() function, update health check URL
if curl -sf http://localhost:8005/ > /dev/null 2>&1; then
```

### Step 3: Deploy to a Different Directory

Deploy your customized server to a different directory:

```bash
# Copy to a different remote directory
./copy_to_remote.sh username@10.100.1.121 /home/username/mcp-financial

# SSH and deploy
ssh username@10.100.1.121 'cd /home/username/mcp-financial && chmod +x deploy.sh && ./deploy.sh start'
```

### Step 4: Update Claude Desktop Configuration

Add the new server to your Claude Desktop config:

```json
{
  "mcpServers": {
    "simple-mcp-server": {
      "url": "http://10.100.1.121:8000/mcp",
      "env": {
        "OPENWEATHER_API_KEY": "your_api_key_here"
      }
    },
    "financial-mcp-server": {
      "url": "http://10.100.1.121:8005/mcp",
      "env": {}
    }
  }
}
```

### Example: Multiple Server Setup

Here's a complete example of different server configurations:

| Server              | Port | Directory                      | Container Name         | Tools                         |
| ------------------- | ---- | ------------------------------ | ---------------------- | ----------------------------- |
| **Original**        | 8000 | `/home/username/mcp`           | `simple-mcp-server`    | Math, Weather                 |
| **Financial**       | 8005 | `/home/username/mcp-financial` | `financial-mcp-server` | Compound Interest, Stock Info |
| **Text Processing** | 8010 | `/home/username/mcp-text`      | `text-mcp-server`      | Text Analysis, Word Count     |
| **Data Analysis**   | 8015 | `/home/username/mcp-data`      | `data-mcp-server`      | Statistics, Data Validation   |

### Port Management Tips

**Check multiple ports at once:**

```bash
# Check common MCP ports
for port in 8000 8005 8010 8015 8020; do
  echo -n "Port $port: "
  if sudo netstat -tulpn | grep -q ":$port "; then
    echo "OCCUPIED"
  else
    echo "FREE"
  fi
done
```

**Reserve ports in your documentation:**

```bash
# Create a port registry file
echo "8000 - simple-mcp-server (math/weather)" >> ~/mcp-ports.txt
echo "8005 - financial-mcp-server (finance)" >> ~/mcp-ports.txt
echo "8010 - text-mcp-server (text processing)" >> ~/mcp-ports.txt
```

### Testing Multiple Servers

Test each server independently:

```bash
# Test original server
curl http://10.100.1.121:8000/
npx @modelcontextprotocol/inspector http://10.100.1.121:8000/mcp

# Test financial server
curl http://10.100.1.121:8005/
npx @modelcontextprotocol/inspector http://10.100.1.121:8005/mcp
```

This approach allows you to run multiple specialized MCP servers on the same machine, each serving different purposes and tools.

## Remote Deployment

### Docker Deployment Scripts

The project includes several deployment scripts for easy remote deployment:

#### **copy_to_remote.sh** - File Copy Only

Copies project files to a remote server:

```bash
# Copy files to default directory (/home/username/mcp)
./copy_to_remote.sh username@10.100.1.121

# Copy files to custom directory
./copy_to_remote.sh username@10.100.1.121 /opt/mcp-server

# Copy to different user/server
./copy_to_remote.sh user@myserver.com /home/user/projects/mcp
```

#### **remote_full_deploy.sh** - Complete Deployment

Copies files AND deploys the server:

```bash
# Full deployment to default directory
./remote_full_deploy.sh username@10.100.1.121

# Full deployment to custom directory
./remote_full_deploy.sh username@10.100.1.121 /opt/mcp-server

# Deploy to different server/path
./remote_full_deploy.sh user@myserver.com /home/user/projects/mcp
```

#### **deploy.sh** - Local Deployment Management

Manages the Docker deployment on the server:

```bash
# On the remote server
./deploy.sh start    # Start server
./deploy.sh stop     # Stop server
./deploy.sh restart  # Restart server
./deploy.sh status   # Check status
./deploy.sh logs     # View server logs
./deploy.sh cleanup  # Clean up containers
./deploy.sh update   # Clean rebuild and restart
```

### Development Workflow

For rapid development with a remote server:

```bash
# 1. Make code changes locally
vim server.py

# 2. Copy files to remote (default path)
./copy_to_remote.sh username@10.100.1.121

# 3. Restart remote server
ssh username@10.100.1.121 'cd /home/username/mcp && ./deploy.sh restart'

# Or with custom path:
./copy_to_remote.sh username@10.100.1.121 /opt/mcp-server
ssh username@10.100.1.121 'cd /opt/mcp-server && ./deploy.sh restart'

# One-liner for default setup:
./copy_to_remote.sh username@10.100.1.121 && ssh username@10.100.1.121 'cd /home/username/mcp && ./deploy.sh restart'
```

### Remote Path Flexibility

Both deployment scripts now accept an optional remote path argument:

- **Default**: `/home/username/mcp` (if no path specified)
- **Custom**: Any path you specify as the second argument

**Examples:**

```bash
# Use default path
./copy_to_remote.sh username@10.100.1.121

# Use custom path
./copy_to_remote.sh username@10.100.1.121 /var/www/mcp-server
./remote_full_deploy.sh username@10.100.1.121 /opt/services/mcp
```

## Troubleshooting

### Permission Denied Errors

If you get "Permission denied" when trying to run `./deploy.sh` on the remote server:

```bash
# SSH to the remote server
ssh username@10.100.1.121

# Navigate to the MCP directory
cd /home/username/mcp

# Make the deploy script executable
chmod +x deploy.sh

# Now you can run the script
./deploy.sh start
```

### Docker Permission Issues

If you get Docker permission errors:

```bash
# Method 1: Add user to docker group (recommended for permanent fix)
sudo usermod -aG docker username

# After adding to docker group, you need to log out and log back in, or run:
newgrp docker

# Method 2: Use the deploy script's fix-docker command
ssh username@10.100.1.121 'cd /home/username/mcp && ./deploy.sh fix-docker'

# Method 3: Logout and login again to refresh group membership
ssh username@10.100.1.121 'newgrp docker'

# Verify docker access without sudo
docker --version
docker ps
```

**Note**: After running `sudo usermod -aG docker username`, you must either:

- Log out and log back in to the system, OR
- Run `newgrp docker` to refresh your group membership

If you continue to have permission issues, you can always run Docker commands with `sudo` as a temporary workaround.

### Container Health Issues

If `deploy.sh status` shows "unhealthy":

```bash
# Check logs for errors
ssh username@10.100.1.121 'cd /home/username/mcp && ./deploy.sh logs'

# Try a clean rebuild
ssh username@10.100.1.121 'cd /home/username/mcp && ./deploy.sh update'
```

### Common Issues

- **Port already in use**: Check if another service is using port 8000
- **File not found**: Ensure you're in the correct directory on remote server
- **Docker not running**: Install Docker using `./deploy.sh` or manually

## Transport Features

This server uses **Streamable HTTP** transport which provides:

- ✅ Web-based access
- ✅ RESTful endpoint at `/mcp`
- ✅ Better performance for web services
- ✅ Support for multiple concurrent clients
- ✅ External network access capability

## Notes

- Server runs on HTTP transport at `http://0.0.0.0:8000` by default
- Weather tool provides mock data if no API key is configured
- All errors are handled gracefully with descriptive messages
- Requires Python 3.11+ for FastMCP compatibility
- Uses Streamable HTTP (recommended by FastMCP for web services)

## Requirements

- Python 3.11+
- FastMCP 2.10.6+
- requests library
- python-dotenv

## Configuration

The server will work out of the box with mock weather data. For real weather data, you'll need to:

1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your free API key
3. Set the `OPENWEATHER_API_KEY` environment variable
