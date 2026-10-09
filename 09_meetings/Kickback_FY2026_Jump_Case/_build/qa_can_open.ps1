param([Parameter(Mandatory=$true)][string]$Pptx)
# Returns 0 if PowerPoint can open the file, 1 otherwise.
try {
    $app = New-Object -ComObject PowerPoint.Application
    $pres = $app.Presentations.Open($Pptx, $true, $false, $false)
    Write-Output ("OPEN_OK slides=" + $pres.Slides.Count)
    $pres.Close()
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
    exit 0
} catch {
    Write-Output ("OPEN_FAIL " + $_.Exception.Message)
    try { $app.Quit() } catch {}
    exit 1
}
