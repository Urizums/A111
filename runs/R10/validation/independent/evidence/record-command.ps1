[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RecordPath,
    [Parameter(Mandatory = $true)][string]$StdoutPath,
    [Parameter(Mandatory = $true)][string]$StderrPath,
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string[]]$ArgumentList
)
$begin = [DateTimeOffset]::UtcNow.ToString('o')
$cwd = (Get-Location).Path
$envSnapshot = [ordered]@{}
$secretPattern = '(?i)(token|secret|password|passwd|credential|api[_-]?key|private[_-]?key|auth|identity|verification)'
$allEnv = [System.Environment]::GetEnvironmentVariables()
foreach ($key in ($allEnv.Keys | Sort-Object)) {
    $name = [string]$key
    $value = [string]$allEnv[$key]
    if ($name -match $secretPattern) { $value = '<redacted>' }
    $envSnapshot[$name] = $value
}
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $FilePath
$psi.WorkingDirectory = $cwd
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
foreach ($arg in $ArgumentList) { [void]$psi.ArgumentList.Add([string]$arg) }
$proc = [System.Diagnostics.Process]::new()
$proc.StartInfo = $psi
$exitCode = $null
$stdout = ''
$stderr = ''
try {
    [void]$proc.Start()
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()
    $proc.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $exitCode = $proc.ExitCode
} catch {
    $stderr += $_.ToString()
    $exitCode = 1
} finally {
    $proc.Dispose()
}
[System.IO.File]::WriteAllText($StdoutPath, $stdout, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($StderrPath, $stderr, [System.Text.UTF8Encoding]::new($false))
$end = [DateTimeOffset]::UtcNow.ToString('o')
$record = [ordered]@{
    argv = @($FilePath) + @($ArgumentList)
    cwd = $cwd
    begin = $begin
    end = $end
    exit_code = $exitCode
    environment = $envSnapshot
    environment_note = 'Inherited process environment captured; values whose names look secret-, identity-, or verification-bearing are redacted.'
    stdout_path = $StdoutPath
    stderr_path = $StderrPath
}
$json = $record | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($RecordPath, $json, [System.Text.UTF8Encoding]::new($false))
exit $exitCode