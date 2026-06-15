$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    "README.md",
    "docs/INSTALL_CN.md",
    "dist/cityu-campus-assistant.md",
    "scripts/build-knowledge.ps1",
    "scripts/build-knowledge.sh",
    "config/mcp.filesystem.example.json",
    "skills/cityu-macau-campus-assistant/SKILL.md",
    "skills/cityu-macau-campus-assistant/agents/openai.yaml",
    "skills/cityu-macau-campus-assistant/references/freshman.md",
    "skills/cityu-macau-campus-assistant/references/fds.md"
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
    "<!-- SOURCE: skills/cityu-macau-campus-assistant/SKILL.md -->",
    "<!-- SOURCE: skills/cityu-macau-campus-assistant/references/freshman.md -->",
    "<!-- SOURCE: skills/cityu-macau-campus-assistant/references/fds.md -->"
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
    "skills/cityu-macau-campus-assistant/SKILL.md",
    "skills/cityu-macau-campus-assistant/references/freshman.md",
    "skills/cityu-macau-campus-assistant/references/fds.md"
)) {
    $source = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot $sourcePath)
    $source = $source -replace "`r`n", "`n"
    $source = ($source -replace "[ `t]+(?=`n|$)", "").Trim()
    if (-not $bundle.Contains($source.Trim())) {
        throw "Bundle does not contain the complete source: $sourcePath"
    }
    if ($sourcePath.Contains("/references/") -and -not $source.Contains("Retrieval Map")) {
        throw "Large reference is missing a retrieval map: $sourcePath"
    }
}

$skillPath = Join-Path $repoRoot "skills/cityu-macau-campus-assistant/SKILL.md"
$skill = Get-Content -Raw -Encoding utf8 $skillPath
if (-not $skill.StartsWith("---`nname: cityu-macau-campus-assistant`ndescription: Use when")) {
    throw "SKILL.md must use valid frontmatter with a trigger-focused description"
}
foreach ($requiredText in @(
    "references/freshman.md",
    "references/fds.md",
    "City University of Macau",
    "admissions",
    "D endorsement",
    "accommodation",
    "publications",
    "graduation requirements"
)) {
    if (-not $skill.Contains($requiredText)) {
        throw "SKILL.md is missing reusable skill guidance: $requiredText"
    }
}
if ($skill.Contains("knowledge-base/")) {
    throw "SKILL.md must use the standard references directory"
}

$openAiYamlPath = Join-Path $repoRoot "skills/cityu-macau-campus-assistant/agents/openai.yaml"
$openAiYaml = Get-Content -Raw -Encoding utf8 $openAiYamlPath
foreach ($requiredText in @(
    "display_name:",
    'short_description:',
    'default_prompt: "Use $cityu-macau-campus-assistant'
)) {
    if (-not $openAiYaml.Contains($requiredText)) {
        throw "agents/openai.yaml is missing required metadata: $requiredText"
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
