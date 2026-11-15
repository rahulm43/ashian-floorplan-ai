Set-Location "C:\Users\Lenovo\.gemini\antigravity\scratch\ashian-floorplan-ai"
$json = Get-Content -Raw -Path "all_captured_urls.json" | ConvertFrom-Json

New-Item -ItemType Directory -Force -Path "dataset/masks" | Out-Null
New-Item -ItemType Directory -Force -Path "dataset/images" | Out-Null

$yProps = $json.y.psobject.properties
Write-Output "Found $($yProps.Count) masks to download."

foreach ($prop in $yProps) {
    $fname = $prop.Name
    $url = $prop.Value
    $dest = "dataset/masks/$fname"
    if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 1000)) {
        continue
    }
    Write-Output "Downloading mask $fname..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UserAgent "Mozilla/5.0" -TimeoutSec 30
    } catch {
        Write-Output "Error downloading $fname : $_"
    }
}

$xProps = $json.x.psobject.properties
Write-Output "Found $($xProps.Count) images to check."

foreach ($prop in $xProps) {
    $fname = $prop.Name
    $url = $prop.Value
    $dest = "dataset/images/$fname"
    if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 1000)) {
        continue
    }
    Write-Output "Downloading image $fname..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UserAgent "Mozilla/5.0" -TimeoutSec 30
    } catch {
        Write-Output "Error downloading $fname : $_"
    }
}

$maskCount = (Get-ChildItem "dataset/masks").Count
$imgCount = (Get-ChildItem "dataset/images").Count
Write-Output "DOWNLOAD COMPLETE!"
Write-Output "Total masks on disk: $maskCount"
Write-Output "Total images on disk: $imgCount"
