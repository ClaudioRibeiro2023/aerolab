<#
.SYNOPSIS
    Blue-Green Deployment Script for Template Platform

.DESCRIPTION
    Performs zero-downtime deployments using blue-green strategy.
    Supports rollback, health checks, and gradual traffic shifting.

.PARAMETER Action
    The deployment action: deploy, switch, rollback, status

.PARAMETER Version
    The new version tag to deploy

.PARAMETER Namespace
    Kubernetes namespace (default: template-platform)

.EXAMPLE
    ./blue-green-deploy.ps1 -Action deploy -Version v1.2.0
    ./blue-green-deploy.ps1 -Action switch
    ./blue-green-deploy.ps1 -Action rollback
    ./blue-green-deploy.ps1 -Action status
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("deploy", "switch", "rollback", "status")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "template-platform",
    
    [Parameter(Mandatory=$false)]
    [int]$HealthCheckTimeout = 120,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Status($message) { Write-Host "[STATUS] $message" -ForegroundColor Cyan }
function Write-Success($message) { Write-Host "[SUCCESS] $message" -ForegroundColor Green }
function Write-Warning($message) { Write-Host "[WARNING] $message" -ForegroundColor Yellow }
function Write-Error($message) { Write-Host "[ERROR] $message" -ForegroundColor Red }

# Get current active version (blue or green)
function Get-ActiveVersion {
    $selector = kubectl get svc api-service -n $Namespace -o jsonpath='{.spec.selector.version}' 2>$null
    return $selector
}

# Get inactive version
function Get-InactiveVersion {
    $active = Get-ActiveVersion
    if ($active -eq "blue") { return "green" }
    return "blue"
}

# Check deployment health
function Test-DeploymentHealth {
    param([string]$Deployment)
    
    Write-Status "Checking health of $Deployment..."
    
    $timeout = $HealthCheckTimeout
    $interval = 5
    $elapsed = 0
    
    while ($elapsed -lt $timeout) {
        $ready = kubectl get deployment $Deployment -n $Namespace -o jsonpath='{.status.readyReplicas}' 2>$null
        $desired = kubectl get deployment $Deployment -n $Namespace -o jsonpath='{.spec.replicas}' 2>$null
        
        if ($ready -eq $desired -and [int]$ready -gt 0) {
            Write-Success "$Deployment is healthy ($ready/$desired replicas ready)"
            return $true
        }
        
        Write-Status "Waiting for $Deployment... ($ready/$desired ready, ${elapsed}s elapsed)"
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }
    
    Write-Error "$Deployment failed health check after ${timeout}s"
    return $false
}

# Deploy new version to inactive slot
function Deploy-NewVersion {
    param([string]$Version)
    
    $inactive = Get-InactiveVersion
    Write-Status "Deploying version $Version to $inactive slot..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would deploy to $inactive"
        return
    }
    
    # Update image tags
    kubectl set image deployment/api-$inactive api=template-platform/api:$Version -n $Namespace
    kubectl set image deployment/web-$inactive web=template-platform/web:$Version -n $Namespace
    
    # Scale up inactive deployment
    kubectl scale deployment api-$inactive --replicas=2 -n $Namespace
    kubectl scale deployment web-$inactive --replicas=2 -n $Namespace
    
    # Wait for health
    $apiHealthy = Test-DeploymentHealth "api-$inactive"
    $webHealthy = Test-DeploymentHealth "web-$inactive"
    
    if (-not $apiHealthy -or -not $webHealthy) {
        Write-Error "Deployment failed health checks. Rolling back..."
        kubectl scale deployment api-$inactive --replicas=0 -n $Namespace
        kubectl scale deployment web-$inactive --replicas=0 -n $Namespace
        throw "Deployment failed"
    }
    
    Write-Success "Version $Version deployed to $inactive slot"
    Write-Status "Test at preview URLs before switching traffic"
    Write-Status "Run: ./blue-green-deploy.ps1 -Action switch"
}

# Switch traffic to new version
function Switch-Traffic {
    $active = Get-ActiveVersion
    $inactive = Get-InactiveVersion
    
    Write-Status "Switching traffic from $active to $inactive..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would switch from $active to $inactive"
        return
    }
    
    # Verify inactive is healthy before switch
    $apiHealthy = Test-DeploymentHealth "api-$inactive"
    $webHealthy = Test-DeploymentHealth "web-$inactive"
    
    if (-not $apiHealthy -or -not $webHealthy) {
        throw "Cannot switch: $inactive deployment is not healthy"
    }
    
    # Switch service selectors
    kubectl patch svc api-service -n $Namespace -p "{`"spec`":{`"selector`":{`"version`":`"$inactive`"}}}"
    kubectl patch svc web-service -n $Namespace -p "{`"spec`":{`"selector`":{`"version`":`"$inactive`"}}}"
    
    Write-Success "Traffic switched to $inactive"
    
    # Scale down old deployment after brief delay
    Write-Status "Waiting 30s before scaling down $active..."
    Start-Sleep -Seconds 30
    
    kubectl scale deployment api-$active --replicas=0 -n $Namespace
    kubectl scale deployment web-$active --replicas=0 -n $Namespace
    
    Write-Success "Deployment complete! Old version ($active) scaled down"
}

# Rollback to previous version
function Invoke-Rollback {
    $active = Get-ActiveVersion
    $inactive = Get-InactiveVersion
    
    Write-Status "Rolling back from $active to $inactive..."
    
    if ($DryRun) {
        Write-Warning "[DRY RUN] Would rollback from $active to $inactive"
        return
    }
    
    # Scale up inactive (previous version)
    kubectl scale deployment api-$inactive --replicas=2 -n $Namespace
    kubectl scale deployment web-$inactive --replicas=2 -n $Namespace
    
    # Wait for health
    $apiHealthy = Test-DeploymentHealth "api-$inactive"
    $webHealthy = Test-DeploymentHealth "web-$inactive"
    
    if (-not $apiHealthy -or -not $webHealthy) {
        throw "Rollback failed: previous version is not healthy"
    }
    
    # Switch traffic
    kubectl patch svc api-service -n $Namespace -p "{`"spec`":{`"selector`":{`"version`":`"$inactive`"}}}"
    kubectl patch svc web-service -n $Namespace -p "{`"spec`":{`"selector`":{`"version`":`"$inactive`"}}}"
    
    # Scale down current (failed) version
    kubectl scale deployment api-$active --replicas=0 -n $Namespace
    kubectl scale deployment web-$active --replicas=0 -n $Namespace
    
    Write-Success "Rollback complete! Traffic now on $inactive"
}

# Show deployment status
function Show-Status {
    Write-Status "Blue-Green Deployment Status"
    Write-Host ""
    
    $active = Get-ActiveVersion
    Write-Host "Active Version: " -NoNewline
    Write-Host $active -ForegroundColor Green
    Write-Host ""
    
    Write-Host "=== API Deployments ===" -ForegroundColor Cyan
    kubectl get deployment -n $Namespace -l app=api -o wide
    Write-Host ""
    
    Write-Host "=== Web Deployments ===" -ForegroundColor Cyan
    kubectl get deployment -n $Namespace -l app=web -o wide
    Write-Host ""
    
    Write-Host "=== Services ===" -ForegroundColor Cyan
    kubectl get svc -n $Namespace
    Write-Host ""
    
    Write-Host "=== Pods ===" -ForegroundColor Cyan
    kubectl get pods -n $Namespace -o wide
}

# Main execution
try {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Blue-Green Deployment - $Action" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    switch ($Action) {
        "deploy" {
            Deploy-NewVersion -Version $Version
        }
        "switch" {
            Switch-Traffic
        }
        "rollback" {
            Invoke-Rollback
        }
        "status" {
            Show-Status
        }
    }
    
    Write-Host ""
    Write-Success "Action '$Action' completed successfully!"
    
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
