param(
  [string]$CatalogBase = "http://localhost:8004",
  [string]$InventoryBase = "http://localhost:8010",
  [string]$OutputDir = "services/pricing/testing/testdata/.generated"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Invoke-JsonPost {
  param(
    [string]$Url,
    [hashtable]$Body
  )
  $json = $Body | ConvertTo-Json -Depth 10
  return Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/json" -Body $json
}

function Invoke-InventoryImportMultipart {
  param(
    [string]$Url,
    [string]$CsvPath,
    [string]$FileName
  )

  Add-Type -AssemblyName System.Net.Http

  $httpClient = New-Object System.Net.Http.HttpClient
  try {
    $multipart = New-Object System.Net.Http.MultipartFormDataContent
    try {
      $fileBytes = [System.IO.File]::ReadAllBytes($CsvPath)
      $fileContent = New-Object System.Net.Http.ByteArrayContent -ArgumentList (,$fileBytes)
      $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/csv")
      $multipart.Add($fileContent, "file", $FileName)
      $multipart.Add((New-Object System.Net.Http.StringContent($FileName)), "file_name")

      $response = $httpClient.PostAsync($Url, $multipart).Result
      if (-not $response) {
        throw "Inventory import request returned null response."
      }
      $responseBody = ""
      if ($response.Content) {
        $responseBody = $response.Content.ReadAsStringAsync().Result
      }
      if (-not $response.IsSuccessStatusCode) {
        throw "Inventory import failed ($([int]$response.StatusCode)): $responseBody"
      }
      if ([string]::IsNullOrWhiteSpace($responseBody)) {
        return @{ status = "ok"; detail = "empty response body" }
      }
      return $responseBody | ConvertFrom-Json
    } finally {
      $multipart.Dispose()
    }
  } finally {
    $httpClient.Dispose()
  }
}

Write-Host "Creating test category in catalog..."
$categoryName = "Pricing QA"
try {
  $category = Invoke-JsonPost -Url "$CatalogBase/api/catalog/categories" -Body @{
    name = $categoryName
    description = "Category for pricing integration tests"
  }
} catch {
  Write-Host "Category already exists or cannot be created. Reusing existing category..."
  $categories = Invoke-RestMethod -Method Get -Uri "$CatalogBase/api/catalog/categories"
  $category = $categories | Where-Object { $_.name -eq $categoryName } | Select-Object -First 1
  if (-not $category) {
    throw "Could not create or resolve category '$categoryName'."
  }
}

Write-Host "Creating test books in catalog..."
$book1 = Invoke-JsonPost -Url "$CatalogBase/api/catalog/books" -Body @{
  title = "Clean Architecture"
  subtitle = ""
  author = "Robert C. Martin"
  publisher = "Prentice Hall"
  publication_year = 2021
  volume = ""
  isbn = "9780134494166"
  issn = ""
  category_id = $category.id
  description = "Test book 1"
  cover_url = ""
  summary = ""
  language = "es"
  page_count = 432
  published_date = "2021-01-01"
  authors_extra = @()
  categories_external = @()
  thumbnail_url = ""
  source_provider = "manual_seed"
  source_reference = "pricing_test"
  enrichment_status = "completed"
  enrichment_score = 0.9
  last_enriched_at = ""
  enriched_flag = $true
  published_flag = $true
}

$book2 = Invoke-JsonPost -Url "$CatalogBase/api/catalog/books" -Body @{
  title = "Domain-Driven Design"
  subtitle = ""
  author = "Eric Evans"
  publisher = "Addison-Wesley"
  publication_year = 2018
  volume = ""
  isbn = "9780321125217"
  issn = ""
  category_id = $category.id
  description = "Test book 2"
  cover_url = ""
  summary = ""
  language = "en"
  page_count = 560
  published_date = "2018-01-01"
  authors_extra = @()
  categories_external = @()
  thumbnail_url = ""
  source_provider = "manual_seed"
  source_reference = "pricing_test"
  enrichment_status = "pending"
  enrichment_score = 0.2
  last_enriched_at = ""
  enriched_flag = $false
  published_flag = $true
}

$book3 = Invoke-JsonPost -Url "$CatalogBase/api/catalog/books" -Body @{
  title = "Refactoring"
  subtitle = ""
  author = "Martin Fowler"
  publisher = "Addison-Wesley"
  publication_year = 2005
  volume = ""
  isbn = "9780201485677"
  issn = ""
  category_id = $category.id
  description = "Test book 3"
  cover_url = ""
  summary = ""
  language = "en"
  page_count = 448
  published_date = "2005-01-01"
  authors_extra = @()
  categories_external = @()
  thumbnail_url = ""
  source_provider = "manual_seed"
  source_reference = "pricing_test"
  enrichment_status = "completed"
  enrichment_score = 0.8
  last_enriched_at = ""
  enriched_flag = $true
  published_flag = $true
}

Write-Host "Building inventory CSV..."
$csvPath = Join-Path $OutputDir "inventory_pricing_seed.csv"
$csvContent = @(
  "external_code,book_reference,quantity_available,quantity_reserved,condition,defects,observations"
  "INV-BOOK1-001,$($book1.id),2,0,used_good,,minor wear"
  "INV-BOOK1-002,$($book1.id),1,0,new,,sealed"
  "INV-BOOK2-001,$($book2.id),8,1,like_new,,great condition"
  "INV-BOOK3-001,$($book3.id),12,1,used_fair,cover damage,old copy"
) -join "`n"

Set-Content -Path $csvPath -Value $csvContent -Encoding UTF8

Write-Host "Importing inventory CSV..."
$inventoryImport = $null
try {
  $inventoryImport = Invoke-InventoryImportMultipart -Url "$InventoryBase/api/inventory/imports" -CsvPath $csvPath -FileName "inventory_pricing_seed.csv"
} catch {
  Write-Warning ("Inventory import failed, continuing with catalog-only seed: " + $_.Exception.Message)
  $inventoryImport = @{
    status = "failed"
    detail = $_.Exception.Message
  }
}

$output = @{
  created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  category = $category
  books = @(
    @{ key = "BOOK_ID_1"; id = $book1.id; title = $book1.title },
    @{ key = "BOOK_ID_2"; id = $book2.id; title = $book2.title },
    @{ key = "BOOK_ID_3"; id = $book3.id; title = $book3.title }
  )
  inventory_import = $inventoryImport
} | ConvertTo-Json -Depth 20

$outputPath = Join-Path $OutputDir "pricing_seed_output.json"
Set-Content -Path $outputPath -Value $output -Encoding UTF8

Write-Host ""
Write-Host "Seed completed."
Write-Host "BOOK_ID_1 = $($book1.id)"
Write-Host "BOOK_ID_2 = $($book2.id)"
Write-Host "BOOK_ID_3 = $($book3.id)"
Write-Host "Output file: $outputPath"
