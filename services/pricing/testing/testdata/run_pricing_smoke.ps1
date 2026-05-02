param(
  [string]$PricingBase = "http://localhost:8003",
  [string]$SeedOutput = "services/pricing/testing/testdata/.generated/pricing_seed_output.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SeedOutput)) {
  throw "Seed output not found: $SeedOutput. Run seed_pricing_data.ps1 first."
}

$seed = Get-Content $SeedOutput -Raw | ConvertFrom-Json
$book1 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_1" })[0].id
$book2 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_2" })[0].id
$book3 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_3" })[0].id

Write-Host "1) GET /api/pricing/health"
$health = Invoke-RestMethod -Method Get -Uri "$PricingBase/api/pricing/health"
$health | ConvertTo-Json -Depth 10

Write-Host "2) POST /api/pricing/calculate (OK)"
$calc = Invoke-RestMethod -Method Post -Uri "$PricingBase/api/pricing/calculate" -ContentType "application/json" -Body (@{
  book_reference = $book1
} | ConvertTo-Json)
$calc | ConvertTo-Json -Depth 20

Write-Host "3) POST /api/pricing/calculate/batch (mixed)"
$batch = Invoke-RestMethod -Method Post -Uri "$PricingBase/api/pricing/calculate/batch" -ContentType "application/json" -Body (@{
  book_references = @($book1, $book2, $book3, "BOOK-NOT-FOUND-999")
} | ConvertTo-Json)
$batch | ConvertTo-Json -Depth 20

Write-Host "4) GET /api/pricing/decisions"
$decisions = Invoke-RestMethod -Method Get -Uri "$PricingBase/api/pricing/decisions?limit=20&offset=0"
$decisions | ConvertTo-Json -Depth 20

Write-Host "5) GET /api/pricing/decisions/{book_reference}"
$decisionOne = Invoke-RestMethod -Method Get -Uri "$PricingBase/api/pricing/decisions/$book1"
$decisionOne | ConvertTo-Json -Depth 20

Write-Host "6) GET /pricing/products"
$legacy = Invoke-RestMethod -Method Get -Uri "$PricingBase/pricing/products?product_ids=$book1,$book2"
$legacy | ConvertTo-Json -Depth 20

Write-Host "7) POST /api/pricing/calculate (error expected for blank book_reference)"
try {
  Invoke-RestMethod -Method Post -Uri "$PricingBase/api/pricing/calculate" -ContentType "application/json" -Body (@{
    book_reference = "   "
  } | ConvertTo-Json) | Out-Null
  Write-Host "Unexpected: blank book_reference did not fail."
} catch {
  Write-Host "Expected error captured."
  if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
    Write-Host ("StatusCode: " + [int]$_.Exception.Response.StatusCode)
  }
  Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "Smoke run completed."
