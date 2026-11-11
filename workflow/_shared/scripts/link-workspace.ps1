[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)][string]$WorkspacePath,
    [string]$RepositoryPath = (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent)
)
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath($WorkspacePath)
$repo = [IO.Path]::GetFullPath($RepositoryPath)
$library = Join-Path $repo 'workflow'
if (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) { throw 'RepositoryPath doit être un clone Git.' }
if (-not (Test-Path -LiteralPath (Join-Path $library '3d-reference-to-model/SKILL.md'))) { throw 'Bibliothèque workflow absente.' }
if (-not (Test-Path -LiteralPath $workspace -PathType Container)) { throw 'Espace de travail absent.' }
$skillsPath = [IO.Path]::GetFullPath((Join-Path $workspace '.agents/skills'))
$backupRoot = [IO.Path]::GetFullPath((Join-Path $workspace '.local-checks/skills-backups'))
if (-not $skillsPath.StartsWith(($workspace.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Chemin des skills hors espace.' }
if (-not $backupRoot.StartsWith(($workspace.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Chemin de sauvegarde hors espace.' }
if (Test-Path -LiteralPath $skillsPath) {
    $current = Get-Item -LiteralPath $skillsPath -Force
    if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        $destination = [IO.Path]::GetFullPath([string]@($current.Target)[0])
        if ($destination.TrimEnd('\') -eq $library.TrimEnd('\')) {
            Write-Output "Déjà lié : $skillsPath -> $library"
            return
        }
        throw 'Une autre liaison existe ; aucune ressource modifiée.'
    }
    foreach ($file in Get-ChildItem -LiteralPath $skillsPath -Recurse -File -Force) {
        if ($file.FullName -match '[\\/]__pycache__[\\/]' -or $file.Extension -in '.pyc', '.pyo') { continue }
        $relative = $file.FullName.Substring($skillsPath.Length).TrimStart('\', '/')
        $copy = Join-Path $library $relative
        if (-not (Test-Path -LiteralPath $copy -PathType Leaf)) { throw "Fichier local sans copie Git : $relative" }
        if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash) {
            throw "Divergence locale préservée : $relative. Réconcilier les fichiers avant la liaison."
        }
    }
}
if (-not $PSCmdlet.ShouldProcess($skillsPath, "Lier à $library avec sauvegarde préalable")) { return }
New-Item -ItemType Directory -Path (Split-Path $skillsPath -Parent) -Force | Out-Null
$backup = $null
if (Test-Path -LiteralPath $skillsPath) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    $backup = [IO.Path]::GetFullPath((Join-Path $backupRoot ('skills-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8))))
    if (-not $backup.StartsWith(($backupRoot.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Sauvegarde hors du dossier prévu.' }
    if ((Get-Item -LiteralPath $skillsPath).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'La source a changé pendant la vérification.' }
    Move-Item -LiteralPath $skillsPath -Destination $backup
}
try {
    New-Item -ItemType Junction -Path $skillsPath -Target $library | Out-Null
}
catch {
    if ($backup -and -not (Test-Path -LiteralPath $skillsPath)) {
        Move-Item -LiteralPath $backup -Destination $skillsPath
    }
    throw
}
[pscustomobject]@{ Skills = $skillsPath; GitWorkflow = $library; Backup = $backup }
