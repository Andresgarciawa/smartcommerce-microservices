param(
  [string]$SeedOutput = "services/pricing/testing/testdata/.generated/pricing_seed_output.json",
  [string]$PayloadDir = "services/pricing/testing/testdata/payloads"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SeedOutput)) {
  throw "Seed output not found: $SeedOutput. Run seed_pricing_data.ps1 first."
}

New-Item -ItemType Directory -Force -Path $PayloadDir | Out-Null

$seed = Get-Content $SeedOutput -Raw | ConvertFrom-Json
$book1 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_1" })[0].id
$book2 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_2" })[0].id
$book3 = ($seed.books | Where-Object { $_.key -eq "BOOK_ID_3" })[0].id

if (-not $book1 -or -not $book2 -or -not $book3) {
  throw "Could not resolve BOOK_ID_1/2/3 from seed output."
}

$calculateOk = @{
  book_reference = $book1
}

$calculateNotFound = @{
  book_reference = "BOOK-NOT-FOUND-999"
}

$calculateBadRequest = @{
  book_reference = "   "
}

$batchMixed = @{
  book_references = @($book1, $book2, $book3, "BOOK-NOT-FOUND-999")
}

Set-Content -Path (Join-Path $PayloadDir "calculate_ok.json") -Value ($calculateOk | ConvertTo-Json -Depth 10) -Encoding UTF8
Set-Content -Path (Join-Path $PayloadDir "calculate_not_found.json") -Value ($calculateNotFound | ConvertTo-Json -Depth 10) -Encoding UTF8
Set-Content -Path (Join-Path $PayloadDir "calculate_bad_request.json") -Value ($calculateBadRequest | ConvertTo-Json -Depth 10) -Encoding UTF8
Set-Content -Path (Join-Path $PayloadDir "batch_mixed.json") -Value ($batchMixed | ConvertTo-Json -Depth 10) -Encoding UTF8

Write-Host "Payloads generated in: $PayloadDir"
Write-Host "calculate_ok -> $book1"
Write-Host "batch_mixed -> $book1, $book2, $book3, BOOK-NOT-FOUND-999"
