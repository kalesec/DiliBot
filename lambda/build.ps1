# Builds the two deployment zips for upload to the Lambda console.
#
# Produces:
#   dist/dilibot-interactions.zip  (handler + PyNaCl, built for Lambda's Linux x86_64)
#   dist/dilibot-worker.zip        (handler only -- stdlib and boto3 come with the runtime)
#
# Usage:  .\build.ps1

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$here = $PSScriptRoot
$dist = Join-Path $here "dist"
$build = Join-Path $here "build"

function New-LambdaZip {
    <#
        Zips a directory for Lambda.

        Deliberately not Compress-Archive: on Windows PowerShell 5.1 it writes
        backslash path separators into the archive. The ZIP format requires
        forward slashes, so Lambda's Linux runtime would unpack a file literally
        named "nacl\signing.py" instead of a nacl/ package, and the import would
        fail at runtime. Writing entries by hand keeps the separators correct.
    #>
    param([string]$SourceDir, [string]$ZipPath)

    if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
    $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, "Create")
    try {
        $root = (Resolve-Path $SourceDir).Path.TrimEnd('\') + '\'
        Get-ChildItem -Path $SourceDir -Recurse -File |
            # Compiled bytecode for the wrong interpreter and Windows launcher
            # scripts are dead weight in a Linux package.
            Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and $_.FullName -notmatch '\\bin\\' } |
            ForEach-Object {
                $entryName = $_.FullName.Substring($root.Length).Replace('\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $zip, $_.FullName, $entryName, "Optimal") | Out-Null
            }
    }
    finally {
        $zip.Dispose()
    }
}

# Start clean so removed dependencies never linger in a zip.
if (Test-Path $build) { Remove-Item -Recurse -Force $build }
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Path $dist | Out-Null
New-Item -ItemType Directory -Path $build | Out-Null

# --- interactions function -------------------------------------------------
# PyNaCl ships a compiled extension, so a plain `pip install` on Windows would
# produce a Windows binary that cannot run on Lambda. --platform forces pip to
# fetch the prebuilt Linux wheel instead, which avoids needing Docker or WSL.
Write-Host "Fetching PyNaCl (Linux x86_64 wheel)..."
pip install `
    --target $build `
    --platform manylinux2014_x86_64 `
    --implementation cp `
    --python-version 3.13 `
    --only-binary=:all: `
    --upgrade `
    --quiet `
    pynacl
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

Copy-Item (Join-Path $here "interactions_handler.py") $build

Write-Host "Packaging dilibot-interactions.zip..."
New-LambdaZip -SourceDir $build -ZipPath (Join-Path $dist "dilibot-interactions.zip")

# --- worker function -------------------------------------------------------
# Only stdlib plus boto3, and boto3 is preinstalled in the Lambda runtime.
Write-Host "Packaging dilibot-worker.zip..."
$workerBuild = Join-Path $build "_worker"
New-Item -ItemType Directory -Path $workerBuild | Out-Null
Copy-Item (Join-Path $here "audit_worker.py") $workerBuild
New-LambdaZip -SourceDir $workerBuild -ZipPath (Join-Path $dist "dilibot-worker.zip")

Remove-Item -Recurse -Force $build

# Guard against silently shipping a broken package again.
Write-Host "Verifying archive layout..."
foreach ($zipFile in Get-ChildItem $dist -Filter *.zip) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipFile.FullName)
    try {
        $bad = $zip.Entries | Where-Object { $_.FullName -like '*\*' }
        if ($bad) { throw "$($zipFile.Name) contains backslash paths -- Lambda will fail to import" }
        $sizeMb = "{0:N2}" -f ($zipFile.Length / 1MB)
        Write-Host "  OK  $($zipFile.Name)  ($($zip.Entries.Count) entries, $sizeMb MB)"
    }
    finally { $zip.Dispose() }
}

Write-Host ""
Write-Host "Done. Upload these in the Lambda console:"
Get-ChildItem $dist | ForEach-Object { Write-Host "  $($_.FullName)" }
