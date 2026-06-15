$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    "README.md",
    "docs/INSTALL_CN.md",
    "dist/cityu-campus-assistant.md",
    "scripts/build-knowledge.ps1",
    "scripts/build-knowledge.sh",
    "config/mcp.filesystem.example.json"
)

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "Missing required file: $relativePath"
    }
}

$bundlePath = Join-Path $repoRoot "dist/cityu-campus-assistant.md"
$bundle = Get-Content -Raw -Encoding utf8 $bundlePath
$requiredMarkers = @(
    "<!-- SOURCE: SKILL.md -->",
    "<!-- SOURCE: knowledge-base/freshman.md -->",
    "<!-- SOURCE: knowledge-base/fds.md -->"
)

$lastIndex = -1
foreach ($marker in $requiredMarkers) {
    $index = $bundle.IndexOf($marker, [System.StringComparison]::Ordinal)
    if ($index -lt 0) {
        throw "Bundle is missing marker: $marker"
    }
    if ($index -le $lastIndex) {
        throw "Bundle source markers are out of order: $marker"
    }
    $lastIndex = $index
}

foreach ($sourcePath in @(
    "SKILL.md",
    "knowledge-base/freshman.md",
    "knowledge-base/fds.md"
)) {
    $source = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot $sourcePath)
    $source = $source -replace "`r`n", "`n"
    $source = ($source -replace "[ `t]+(?=`n|$)", "").Trim()
    if (-not $bundle.Contains($source.Trim())) {
        throw "Bundle does not contain the complete source: $sourcePath"
    }
}

$mcpPath = Join-Path $repoRoot "config/mcp.filesystem.example.json"
$mcpRaw = Get-Content -Raw -Encoding utf8 $mcpPath
$mcpConfig = $mcpRaw | ConvertFrom-Json
$mcpArgs = $mcpConfig.mcpServers.'cityu-campus-assistant'.args
if ($mcpArgs -notcontains "@modelcontextprotocol/server-filesystem") {
    throw "MCP template must use @modelcontextprotocol/server-filesystem"
}
if ($mcpRaw.Contains('"@modelcontextprotocol/server-file"')) {
    throw "MCP template contains the obsolete package name"
}

$readme = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot "README.md")
$installGuide = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot "docs/INSTALL_CN.md")

foreach ($requiredText in @(
    "dist/cityu-campus-assistant.md",
    "docs/INSTALL_CN.md",
    "Claude"
)) {
    if (-not $readme.Contains($requiredText)) {
        throw "README is missing required text: $requiredText"
    }
}

foreach ($requiredText in @(
    "Kimi",
    "DeepSeek",
    "Ollama",
    "Open WebUI",
    "Dify",
    "@modelcontextprotocol/server-filesystem"
)) {
    if (-not $installGuide.Contains($requiredText)) {
        throw "Install guide is missing required text: $requiredText"
    }
}

$markdownFiles = @(
    (Join-Path $repoRoot "README.md"),
    (Join-Path $repoRoot "docs/INSTALL_CN.md")
)

foreach ($markdownFile in $markdownFiles) {
    $content = Get-Content -Raw -Encoding utf8 $markdownFile
    $links = [regex]::Matches($content, '\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)')
    foreach ($link in $links) {
        $target = [Uri]::UnescapeDataString($link.Groups[1].Value.Split("#")[0])
        if ([string]::IsNullOrWhiteSpace($target)) {
            continue
        }
        $baseDirectory = Split-Path -Parent $markdownFile
        $resolvedTarget = Join-Path $baseDirectory $target
        if (-not (Test-Path -LiteralPath $resolvedTarget)) {
            throw "Broken relative link in $markdownFile`: $target"
        }
    }
}

Write-Host "Package verification passed."
