$GITHUB_RELEASE = "v0.1.0-beta"
$BASE_DOWNLOAD_URL = "https://github.com/StrijpT-Ellie/contour-wall/releases/$GITHUB_RELEASE/"

function Init-Rust {
    Write-Host "Initialising ContourWall environment for Rust in current directory" -ForegroundColor Blue

    $output = cargo init $project_name --bin 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFailed to initialise the Rust ContourWall development environment." -ForegroundColor Red
        Write-Host "Failed command: `"`"cargo init $project_name --bin`"`""
        Write-Host "exiting..."
        exit 1
    }

    $output = cargo add contourwall 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFailed to add package `"`"contourwall`"`" to your Cargo project" -ForegroundColor Red
        Write-Host "Link to cargo package: https://crates.io/crates/contourwall"
        Write-Host "exiting..."
        exit 1
    }

    Write-Host "Successfully initialised your ContourWall environment for Rust" -ForegroundColor Green
    exit 0
}

function Init-Python {
    Write-Host "Initialising ContourWall environment for Python in current directory" -ForegroundColor Blue
    New-Item -Path . -Name "$project_name.py" -ItemType "file" -Force
    exit 0
}

function Init-Bare {
    Write-Host "Pulling the core library binary" -ForegroundColor Blue
    New-Item -Path . -Name $project_name -ItemType "directory" -Force
    Set-Location -Path $project_name
    $output = Invoke-WebRequest -Uri "$BASE_DOWNLOAD_URL/contourwall_core_linux.so" -OutFile "contourwall_core_linux.so" -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to download binary from Github release $GITHUB_RELEASE" -ForegroundColor Red
        Write-Host "exiting..."
        exit 1
    }
    Write-Host "Successfully initialised your Contour Wall environment" -ForegroundColor Green
    exit 0
}

Write-Host "Welcome to ContourWall!" -ForegroundColor White
Write-Host "`nThis script uses Github release: $GITHUB_RELEASE"
Write-Host "This script will setup the development environment for the ContourWall. If at any time you want to quit this script, press: ctrl + c`n"

Write-Host $BASE_DOWNLOAD_URL

$project_name = Read-Host "What is the name of your project?"

Write-Host ""

$choice = Read-Host "What language do you want to use:
1) Python
2) Rust
3) Bare (no language, just binary)
4) Quit initialisation
"

Write-Host ""

switch ($choice) {
    {$_ -eq 1 -or $_ -eq "python" -or $_ -eq "Python"} {
        Init-Python
    }
    {$_ -eq 2 -or $_ -eq "rust" -or $_ -eq "Rust"} {
        Init-Rust
    }
    {$_ -eq 3 -or $_ -eq "bare" -or $_ -eq "Bare"} {
        Init-Bare
    }
    {$_ -eq 4} {
        exit 0
    }
    default {
        Write-Host "`n'$choice' is not a choice.`nexiting..."
        exit 1
    }
}
