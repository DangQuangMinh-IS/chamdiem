<#
.SYNOPSIS
    Copies the Personal & Team Agent Kit into a project without overwriting existing files.
.PARAMETER Target
    Path to the destination project.
.EXAMPLE
    .\init.ps1 -Target "D:\my-project"
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Target
)

$ErrorActionPreference = "Stop"
$Kit = $PSScriptRoot

if (-not (Test-Path -Path $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}

$AgentsDir = Join-Path $Target ".agents"
if (-not (Test-Path -Path $AgentsDir)) {
    New-Item -ItemType Directory -Path $AgentsDir -Force | Out-Null
}

foreach ($f in @("AGENTS.md", "PROJECT.md")) {
    $DestFile = Join-Path $Target $f
    if (Test-Path -Path $DestFile) {
        Write-Host "skip (exists): $f"
    } else {
        Copy-Item -Path (Join-Path $Kit $f) -Destination $DestFile
        Write-Host "added: $f"
    }
}

# Copy .agents recursively without overwriting existing files
Get-ChildItem -Path (Join-Path $Kit ".agents") -Recurse | ForEach-Object {
    $RelativePath = $_.FullName.Substring((Join-Path $Kit ".agents").Length + 1)
    $DestinationPath = Join-Path $AgentsDir $RelativePath

    if ($_.PSIsContainer) {
        if (-not (Test-Path -Path $DestinationPath)) {
            New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
        }
    } else {
        if (Test-Path -Path $DestinationPath) {
            Write-Host "skip (exists): .agents/$RelativePath"
        } else {
            Copy-Item -Path $_.FullName -Destination $DestinationPath
            Write-Host "added: .agents/$RelativePath"
        }
    }
}

# Copy docs recursively without overwriting existing files
$KitDocs = Join-Path $Kit "docs"
if (Test-Path -Path $KitDocs) {
    $DocsDir = Join-Path $Target "docs"
    if (-not (Test-Path -Path $DocsDir)) {
        New-Item -ItemType Directory -Path $DocsDir -Force | Out-Null
    }
    Get-ChildItem -Path $KitDocs -Recurse | ForEach-Object {
        $RelativePath = $_.FullName.Substring($KitDocs.Length + 1)
        $DestinationPath = Join-Path $DocsDir $RelativePath

        if ($_.PSIsContainer) {
            if (-not (Test-Path -Path $DestinationPath)) {
                New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
            }
        } else {
            if (Test-Path -Path $DestinationPath) {
                Write-Host "skip (exists): docs/$RelativePath"
            } else {
                Copy-Item -Path $_.FullName -Destination $DestinationPath
                Write-Host "added: docs/$RelativePath"
            }
        }
    }
}

Write-Host "Done. Next: fill in $Target\PROJECT.md (or ask the agent to draft it from the repo)."
