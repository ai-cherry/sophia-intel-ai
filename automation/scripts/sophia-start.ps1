# ==============================================
# SOPHIA INTEL AI - WINDOWS POWERSHELL STARTUP
# Cross-platform startup for Windows environments
# ==============================================

param(
    [Parameter()]
    [ValidateSet("development", "docker", "kubernetes", "helm", "auto")]
    [string]$Mode = "auto",
    
    [Parameter()]
    [ValidateSet("development", "staging", "production", "auto")]
    [string]$Environment = "auto",
    
    [Parameter()]
    [ValidateSet("development", "testing", "production")]
    [string]$Profile = "development",
    
    [Parameter()]
    [ValidateSet("start", "stop", "restart", "status", "install", "config", "health")]
    [string]$Command = "start",
    
    [switch]$Verbose,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$AutomationDir = Join-Path $ProjectRoot "automation"

# Global error handling
$ErrorActionPreference = "Stop"

# Logging function
function Write-Log {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR", "DEBUG", "HEADER")]
        [string]$Level,
        
        [Parameter(Mandatory)]
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    switch ($Level) {
        "INFO"    { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Blue }
        "SUCCESS" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "ERROR"   { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "DEBUG"   { if ($Verbose) { Write-Host "[$timestamp] 🔍 $Message" -ForegroundColor Magenta } }
        "HEADER"  { Write-Host "[$timestamp] 🚀 $Message" -ForegroundColor Cyan }
    }
}

# Platform detection
function Get-PlatformType {
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        return "windows"
    } elseif ($IsLinux) {
        return "linux"
    } elseif ($IsMacOS) {
        return "macos"
    } else {
        return "unknown"
    }
}

# Environment detection
function Get-EnvironmentType {
    if ($env:KUBERNETES_SERVICE_HOST) {
        return "kubernetes"
    } elseif ($env:DOCKER_HOST -or (Test-Path "/.dockerenv")) {
        return "docker"
    } elseif (Get-Service -Name "Docker Desktop Service" -ErrorAction SilentlyContinue) {
        return "docker"
    } else {
        return "development"
    }
}

# Check requirements
function Test-Requirements {
    Write-Log "INFO" "Checking system requirements"
    
    $missingDeps = @()
    
    # Check Docker
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        $missingDeps += "docker"
    }
    
    # Check Docker Compose
    if (-not (Get-Command "docker-compose" -ErrorAction SilentlyContinue)) {
        try {
            docker compose version | Out-Null
        } catch {
            $missingDeps += "docker-compose"
        }
    }
    
    # Check Python
    if (-not (Get-Command "python" -ErrorAction SilentlyContinue) -and 
        -not (Get-Command "python3" -ErrorAction SilentlyContinue)) {
        $missingDeps += "python"
    }
    
    # Check curl or equivalent
    if (-not (Get-Command "curl" -ErrorAction SilentlyContinue) -and
        -not (Get-Command "Invoke-WebRequest" -ErrorAction SilentlyContinue)) {
        $missingDeps += "curl"
    }
    
    # Environment-specific requirements
    if ($Mode -eq "kubernetes") {
        if (-not (Get-Command "kubectl" -ErrorAction SilentlyContinue)) {
            $missingDeps += "kubectl"
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Log "ERROR" "Missing dependencies: $($missingDeps -join ', ')"
        Write-Log "INFO" "Please install missing dependencies and try again"
        return $false
    }
    
    Write-Log "SUCCESS" "All system requirements satisfied"
    return $true
}

# Install dependencies
function Install-Dependencies {
    Write-Log "INFO" "Installing system dependencies for Windows"
    
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    
    if (-not $isAdmin) {
        Write-Log "WARNING" "Administrator privileges recommended for installing dependencies"
    }
    
    # Check for package managers
    $hasChoco = Get-Command "choco" -ErrorAction SilentlyContinue
    $hasWinget = Get-Command "winget" -ErrorAction SilentlyContinue
    $hasScoop = Get-Command "scoop" -ErrorAction SilentlyContinue
    
    if ($hasChoco) {
        Write-Log "INFO" "Installing dependencies with Chocolatey"
        choco install docker-desktop python3 curl -y
    } elseif ($hasWinget) {
        Write-Log "INFO" "Installing dependencies with winget"
        winget install Docker.DockerDesktop
        winget install Python.Python.3
        winget install cURL.cURL
    } elseif ($hasScoop) {
        Write-Log "INFO" "Installing dependencies with Scoop"
        scoop install docker python curl
    } else {
        Write-Log "WARNING" "No package manager found. Please install dependencies manually:"
        Write-Log "INFO" "- Docker Desktop: https://www.docker.com/products/docker-desktop"
        Write-Log "INFO" "- Python 3: https://www.python.org/downloads/"
        Write-Log "INFO" "- Git (includes curl): https://git-scm.com/downloads"
        return $false
    }
    
    Write-Log "SUCCESS" "Dependencies installed"
    return $true
}

# Setup configuration
function Set-Configuration {
    Write-Log "INFO" "Setting up configuration for $Environment environment"
    
    $configFile = Join-Path $ProjectRoot ".env.$Environment"
    $templateFile = Join-Path $ProjectRoot ".env.template"
    
    if (-not (Test-Path $configFile) -and (Test-Path $templateFile)) {
        Write-Log "INFO" "Creating environment configuration from template"
        Copy-Item $templateFile $configFile
        
        # Environment-specific adjustments
        $content = Get-Content $configFile
        switch ($Environment) {
            "development" {
                $content = $content -replace "SOPHIA_ENVIRONMENT=production", "SOPHIA_ENVIRONMENT=development"
                $content = $content -replace "LOG_LEVEL=ERROR", "LOG_LEVEL=INFO"
            }
            "production" {
                $content = $content -replace "SOPHIA_ENVIRONMENT=development", "SOPHIA_ENVIRONMENT=production"
                $content = $content -replace "LOG_LEVEL=DEBUG", "LOG_LEVEL=ERROR"
            }
        }
        Set-Content -Path $configFile -Value $content
        
        Write-Log "WARNING" "Please review and update $configFile with your actual configuration"
    }
    
    # Create symbolic link for current environment
    if (Test-Path $configFile) {
        $envLink = Join-Path $ProjectRoot ".env"
        if (Test-Path $envLink) {
            Remove-Item $envLink -Force
        }
        
        # Create hard link (Windows doesn't support symlinks without admin)
        try {
            New-Item -ItemType HardLink -Path $envLink -Value $configFile -Force | Out-Null
            Write-Log "SUCCESS" "Environment configuration linked: .env -> .env.$Environment"
        } catch {
            # Fallback to copy
            Copy-Item $configFile $envLink -Force
            Write-Log "SUCCESS" "Environment configuration copied: .env.$Environment -> .env"
        }
    }
}

# Start services
function Start-Services {
    param(
        [string]$StartMode,
        [string]$StartEnvironment
    )
    
    Write-Log "HEADER" "Starting Sophia Intel AI ($StartMode mode, $StartEnvironment environment)"
    
    Push-Location $ProjectRoot
    
    try {
        switch ($StartMode) {
            "development" -or "docker" {
                $composeFile = "docker-compose.yml"
                $enhancedFile = "docker-compose.enhanced.yml"
                
                if (Test-Path $enhancedFile) {
                    Write-Log "INFO" "Using enhanced Docker Compose configuration"
                    docker-compose -f $enhancedFile up -d
                } else {
                    Write-Log "INFO" "Using standard Docker Compose configuration"
                    docker-compose -f $composeFile up -d
                }
            }
            
            "kubernetes" {
                $k8sDir = Join-Path $ProjectRoot "k8s"
                if (Test-Path $k8sDir) {
                    Write-Log "INFO" "Deploying to Kubernetes"
                    $overlayPath = Join-Path $k8sDir "overlays\$StartEnvironment"
                    kubectl apply -k $overlayPath
                    Write-Log "INFO" "Waiting for deployments to be ready..."
                    kubectl wait --for=condition=available --timeout=300s deployment --all -n sophia-intel-ai
                } else {
                    throw "Kubernetes manifests not found"
                }
            }
            
            "helm" {
                $helmDir = Join-Path $ProjectRoot "helm\sophia-intel-ai"
                if (Test-Path $helmDir) {
                    Write-Log "INFO" "Deploying with Helm"
                    $valuesFile = Join-Path $helmDir "values-$StartEnvironment.yaml"
                    helm upgrade --install sophia-intel-ai $helmDir `
                        --namespace sophia-intel-ai --create-namespace `
                        --values $valuesFile `
                        --wait --timeout 10m
                } else {
                    throw "Helm charts not found"
                }
            }
            
            default {
                throw "Unknown startup mode: $StartMode"
            }
        }
        
        Write-Log "SUCCESS" "Services started successfully"
    } catch {
        Write-Log "ERROR" "Failed to start services: $($_.Exception.Message)"
        throw
    } finally {
        Pop-Location
    }
}

# Verify startup
function Test-Startup {
    Write-Log "INFO" "Verifying system startup"
    
    # Wait for services to be ready
    Start-Sleep -Seconds 30
    
    $pythonCmd = if (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" } else { "python" }
    
    if (Get-Command $pythonCmd -ErrorAction SilentlyContinue) {
        Write-Log "INFO" "Running comprehensive health check"
        $healthScript = Join-Path $AutomationDir "scripts\health-check.py"
        
        try {
            & $pythonCmd $healthScript --check-only --format=text
            Write-Log "SUCCESS" "🎉 All services are healthy!"
            return $true
        } catch {
            Write-Log "ERROR" "❌ Some services are not healthy"
            return $false
        }
    } else {
        Write-Log "WARNING" "Python not available, skipping health check"
        return $true
    }
}

# Show system information
function Show-Info {
    $platform = Get-PlatformType
    $environment = Get-EnvironmentType
    
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  🧠 SOPHIA INTEL AI - WINDOWS STARTUP SCRIPT" -ForegroundColor Cyan
    Write-Host "  📅 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  🖥️  Platform: $platform" -ForegroundColor Cyan
    Write-Host "  🌍 Environment: $environment" -ForegroundColor Cyan
    Write-Host "  📂 Project Root: $ProjectRoot" -ForegroundColor Cyan
    Write-Host "  🔧 Mode: $Mode" -ForegroundColor Cyan
    Write-Host "  📊 Profile: $Profile" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# Show usage information
function Show-Usage {
    @"
Sophia Intel AI Windows PowerShell Startup Script

USAGE:
    .\sophia-start.ps1 [OPTIONS] [COMMAND]

COMMANDS:
    -Command start      Start all services (default)
    -Command stop       Stop all services  
    -Command restart    Restart all services
    -Command status     Show service status
    -Command install    Install system dependencies
    -Command config     Setup configuration
    -Command health     Run health check
    
OPTIONS:
    -Mode <mode>               Startup mode (auto|development|kubernetes|helm)
    -Environment <env>         Environment (auto|development|staging|production)
    -Profile <profile>         Configuration profile (development|testing|production)
    -Verbose                   Enable verbose logging
    -DryRun                    Show what would be done without executing
    -Force                     Force operation even if checks fail
    -Help                      Show this help message

EXAMPLES:
    .\sophia-start.ps1                                    # Auto-detect and start
    .\sophia-start.ps1 -Mode kubernetes -Environment production
    .\sophia-start.ps1 -Profile development -Verbose
    .\sophia-start.ps1 -Command install                   # Install dependencies
    .\sophia-start.ps1 -Command config                    # Setup configuration
    .\sophia-start.ps1 -Command health                    # Run health check

ENVIRONMENT VARIABLES:
    SOPHIA_MODE             Override auto-detected mode
    SOPHIA_ENVIRONMENT      Override auto-detected environment  
    SOPHIA_PROFILE          Configuration profile to use
    SOPHIA_VERBOSE          Enable verbose output (true/false)

"@
}

# Main execution function
function Main {
    # Show help if requested
    if ($Help) {
        Show-Usage
        return
    }
    
    # Override with environment variables
    if ($env:SOPHIA_MODE) { $script:Mode = $env:SOPHIA_MODE }
    if ($env:SOPHIA_ENVIRONMENT) { $script:Environment = $env:SOPHIA_ENVIRONMENT }
    if ($env:SOPHIA_PROFILE) { $script:Profile = $env:SOPHIA_PROFILE }
    if ($env:SOPHIA_VERBOSE -eq "true") { $script:Verbose = $true }
    
    # Auto-detect if needed
    if ($Mode -eq "auto") {
        $script:Mode = Get-EnvironmentType
        Write-Log "DEBUG" "Auto-detected mode: $Mode"
    }
    
    if ($Environment -eq "auto") {
        $script:Environment = if ($env:KUBERNETES_SERVICE_HOST -or $env:USERNAME -eq "root") { "production" } else { "development" }
        Write-Log "DEBUG" "Auto-detected environment: $Environment"
    }
    
    # Show system information
    Show-Info
    
    try {
        # Execute command
        switch ($Command) {
            "start" {
                if ($DryRun) {
                    Write-Log "INFO" "DRY RUN: Would start services in $Mode mode"
                    return
                }
                
                if (-not (Test-Requirements) -and -not $Force) {
                    throw "Requirements check failed"
                }
                
                Set-Configuration
                Start-Services $Mode $Environment
                Test-Startup
            }
            
            "stop" {
                Write-Log "INFO" "Stopping services"
                Push-Location $ProjectRoot
                try {
                    switch ($Mode) {
                        "development" -or "docker" {
                            docker-compose -f "docker-compose.yml" down
                        }
                        "kubernetes" {
                            $overlayPath = "k8s\overlays\$Environment"
                            kubectl delete -k $overlayPath
                        }
                        "helm" {
                            helm uninstall sophia-intel-ai --namespace sophia-intel-ai
                        }
                    }
                } finally {
                    Pop-Location
                }
            }
            
            "restart" {
                & $MyInvocation.MyCommand.Path -Command stop @PSBoundParameters
                Start-Sleep -Seconds 5
                & $MyInvocation.MyCommand.Path -Command start @PSBoundParameters
            }
            
            "status" {
                Write-Log "INFO" "Checking service status"
                Push-Location $ProjectRoot
                try {
                    switch ($Mode) {
                        "development" -or "docker" {
                            docker-compose -f "docker-compose.yml" ps
                        }
                        "kubernetes" {
                            kubectl get all -n sophia-intel-ai
                        }
                    }
                } finally {
                    Pop-Location
                }
            }
            
            "install" {
                Install-Dependencies
            }
            
            "config" {
                Set-Configuration
            }
            
            "health" {
                $pythonCmd = if (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" } else { "python" }
                $healthScript = Join-Path $AutomationDir "scripts\health-check.py"
                & $pythonCmd $healthScript --check-only --format=text
            }
            
            default {
                Write-Log "ERROR" "Unknown command: $Command"
                Show-Usage
                exit 1
            }
        }
    } catch {
        Write-Log "ERROR" $_.Exception.Message
        if ($Verbose) {
            Write-Log "DEBUG" $_.Exception.StackTrace
        }
        exit 1
    }
}

# Signal handlers
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Write-Log "WARNING" "🛑 Startup interrupted by user"
}

# Execute main function
Main