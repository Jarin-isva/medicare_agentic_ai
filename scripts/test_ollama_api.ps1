$ErrorActionPreference = "Stop"

$body = @{ model = "mistral:latest"; prompt = "Say hello"; stream = $false } | ConvertTo-Json -Compress

try {
    $response = Invoke-RestMethod -Method Post -Uri "http://localhost:11434/api/generate" -ContentType "application/json" -Body $body
    $response.response
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
