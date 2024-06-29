# PowerShell Script to Bootstrap Project Structure

# Function to create directory if it doesn't exist
function Create-DirectoryIfNotExists {
    param (
        [string]$path
    )
    if (!(Test-Path -Path $path -PathType Container)) {
        New-Item -ItemType Directory -Path $path
        Write-Output "Created directory: $path"
    } else {
        Write-Output "Directory already exists: $path"
    }
}

# Function to create file with content if it doesn't exist
function Create-FileIfNotExists {
    param (
        [string]$path,
        [string]$content
    )
    if (!(Test-Path -Path $path)) {
        New-Item -ItemType File -Path $path -Value $content
        Write-Output "Created file: $path"
    } else {
        Write-Output "File already exists: $path"
    }
}

# Create directories
Create-DirectoryIfNotExists -path "src"
Create-DirectoryIfNotExists -path "tests"
Create-DirectoryIfNotExists -path "docs"
Create-DirectoryIfNotExists -path "config"

# Create files with placeholder content
Create-FileIfNotExists -path "src/main.ps1" -content "# This is the main script file."
Create-FileIfNotExists -path "tests/test.ps1" -content "# This is the test script file."
Create-FileIfNotExists -path "docs/readme.md" -content "# Project Documentation\nThis project is..."
Create-FileIfNotExists -path "config/settings.json" -content "{}"

Write-Output "Project bootstrap completed."
