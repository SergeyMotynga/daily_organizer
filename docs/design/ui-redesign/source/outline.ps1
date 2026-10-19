param([Parameter(Mandatory=$true)][string]$Directory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$items = Get-Content -LiteralPath (Join-Path $Directory 'texts.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$result = @{}
foreach ($entry in $items.PSObject.Properties) {
    $item = $entry.Value
    $weight = if ($item.bold) { [System.Windows.FontWeights]::Bold } else { [System.Windows.FontWeights]::Normal }
    $face = [System.Windows.Media.Typeface]::new([System.Windows.Media.FontFamily]::new('Arial'), [System.Windows.FontStyles]::Normal, $weight, [System.Windows.FontStretches]::Normal)
    $formatted = [System.Windows.Media.FormattedText]::new([string]$item.text, $culture, [System.Windows.FlowDirection]::LeftToRight, $face, [double]$item.size, [System.Windows.Media.Brushes]::Black, 1.0)
    $geometry = $formatted.BuildGeometry([System.Windows.Point]::new(0, 0))
    $pathGeometry = [System.Windows.Media.PathGeometry]::CreateFromGeometry($geometry)
    $pathData = $pathGeometry.ToString($culture) -replace '^F[01]\s*', ''
    $result[$entry.Name] = @{path=$pathData; top=$geometry.Bounds.Top; width=$formatted.WidthIncludingTrailingWhitespace}
}
$json = ConvertTo-Json -InputObject $result -Depth 4 -Compress
[System.IO.File]::WriteAllText((Join-Path $Directory 'paths.json'), $json, [System.Text.UTF8Encoding]::new($false))
Write-Output ('Outlined {0} unique labels' -f $result.Count)
