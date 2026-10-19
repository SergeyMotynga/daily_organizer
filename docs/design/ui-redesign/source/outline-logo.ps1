$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$face = [System.Windows.Media.Typeface]::new([System.Windows.Media.FontFamily]::new('Arial'), [System.Windows.FontStyles]::Normal, [System.Windows.FontWeights]::Bold, [System.Windows.FontStretches]::Normal)
$formatted = [System.Windows.Media.FormattedText]::new('Daily Organizer', $culture, [System.Windows.FlowDirection]::LeftToRight, $face, 34.0, [System.Windows.Media.Brushes]::Black, 1.0)
$initial = $formatted.BuildGeometry([System.Windows.Point]::new(0,0))
$top = (76 - $initial.Bounds.Height)/2 - $initial.Bounds.Top
$geometry = $formatted.BuildGeometry([System.Windows.Point]::new(91,$top))
$path = [System.Windows.Media.PathGeometry]::CreateFromGeometry($geometry).ToString($culture) -replace '^F[01]\s*', ''
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../assets') -Filter 'route-lockup-*.svg') {
    [xml]$svg = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    $wordmark = $svg.DocumentElement.LastChild
    $wordmark.SetAttribute('d', $path)
    $wordmark.SetAttribute('id', 'wordmark')
    [System.IO.File]::WriteAllText($file.FullName, $svg.OuterXml, [System.Text.UTF8Encoding]::new($false))
}
Write-Output 'Outlined all 4 logo wordmarks as valid SVG paths'
