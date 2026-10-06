[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PacketPath,
    [Parameter(Mandatory = $true)][string]$SnapshotPath
)
$ErrorActionPreference = 'Stop'
$packet = Get-Content -Raw -LiteralPath $PacketPath | ConvertFrom-Json
$items = @($packet.feedback)
$ids = @($items | ForEach-Object { [string]$_.id })
$duplicates = @($items | Where-Object { $_.PSObject.Properties.Name -contains 'duplicate_of' } | ForEach-Object {
    [ordered]@{ id = [string]$_.id; duplicate_of = [string]$_.duplicate_of; source = [string]$_.source }
})
$nullRequiredFields = @($items | Where-Object {
    $_.PSObject.Properties.Name -contains 'device' -and $null -eq $_.device -or
    $_.PSObject.Properties.Name -contains 'version' -and $null -eq $_.version -or
    $_.PSObject.Properties.Name -contains 'steps' -and $null -eq $_.steps
} | ForEach-Object { [string]$_.id })
$index = [ordered]@{
    batch = [string]$packet.batch
    product = [string]$packet.product
    policy_ids = @($packet.policy | ForEach-Object { [string]$_.id })
    input_row_count = $items.Count
    input_ids = $ids
    unique_ids = @($ids | Select-Object -Unique)
    duplicate_relationships = $duplicates
    rows_with_explicit_null_diagnostic_fields = $nullRequiredFields
    sources = @($items | ForEach-Object { [ordered]@{ id = [string]$_.id; source = [string]$_.source } })
}
$json = $index | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($SnapshotPath, $json, [System.Text.UTF8Encoding]::new($false))
Write-Output ("Indexed batch {0}: {1} rows; duplicate links: {2}; explicit null diagnostic rows: {3}." -f $packet.batch, $items.Count, $duplicates.Count, $nullRequiredFields.Count)