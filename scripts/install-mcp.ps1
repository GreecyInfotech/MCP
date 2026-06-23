# Install MCP integration dependencies and verify entry points
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Installing enterprise-ai-platform with MCP integrations..."
.\.venv\Scripts\pip install -e ".[mcp]" -q

Write-Host ""
Write-Host "MCP server entry points (activate .venv first):"
Write-Host "  mcp-github       - GitHub repos, PRs, code search"
Write-Host "  mcp-jira         - Jira issues, sprints, comments"
Write-Host "  mcp-confluence   - Confluence pages and spaces"
Write-Host "  mcp-postgresql   - PostgreSQL schema and read queries"
Write-Host "  mcp-mongodb      - MongoDB collections and queries"
Write-Host "  mcp-kubernetes   - K8s pods, deployments, logs"
Write-Host "  mcp-aws          - S3, EC2, Lambda, CloudWatch"
Write-Host "  mcp-slack        - Slack channels and messaging"
Write-Host "  mcp-browser      - Browser automation (Playwright)"
Write-Host ""
Write-Host "Browser MCP uses installed Chrome/Edge by default (BROWSER_CHANNEL=chrome)."
Write-Host "No 'playwright install chromium' needed unless you prefer bundled Chromium."
Write-Host "If download fails, set in .env:"
Write-Host "  BROWSER_CHANNEL=chrome"
Write-Host "  BROWSER_EXECUTABLE_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
Write-Host ""
Write-Host "Cursor MCP config template: deployment\mcp-config.json"
Write-Host "Copy to ~/.cursor/mcp.json and set env values from .env"
