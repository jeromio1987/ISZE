# Windows OCR with proper IAsyncOperation await
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await-WinRT($asyncOp) {
  $type = $asyncOp.GetType().GenericTypeArguments[0]
  $asTask = $asTaskGeneric.MakeGenericMethod($type)
  $task = $asTask.Invoke($null, @($asyncOp))
  $task.Wait()
  return $task.Result
}

$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.RandomAccessStreamReference, Windows.Foundation, ContentType = WindowsRuntime]

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language 'en-US'))
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
Write-Host ("OCR: " + $engine.RecognizerLanguage.LanguageTag)

$imgDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\pdf_pages'
$outDir = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\pms_intervals_mail_pull\ocr_text'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Priority schedule pages only (engine tables)
$priority = @(
  'N_MY24_p01','N_MY24_p02','N_MY24_p03','N_MY24_p04','N_MY24_p05','N_MY24_p06','N_MY24_p07','N_MY24_p08','N_MY24_p09','N_MY24_p10',
  'N_MY14_p01','N_MY14_p02','N_MY14_p03','N_MY14_p04','N_MY14_p05',
  'F_MY24_p01','F_MY24_p02','F_MY24_p03','F_MY24_p04','F_MY24_p05','F_MY24_p06','F_MY24_p07','F_MY24_p08','F_MY24_p09','F_MY24_p10',
  'F_MY14_p01','F_MY14_p02','F_MY14_p03','F_MY14_p04','F_MY14_p05','F_MY14_p06'
)

$files = Get-ChildItem $imgDir -Filter '*.png' | Where-Object {
  $n = $_.Name
  foreach ($p in $priority) { if ($n -like "*$p*") { return $true } }
  return $false
} | Sort-Object Name

Write-Host ("priority images=" + $files.Count)
foreach ($f in $files) {
  try {
    $sf = Await-WinRT ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName))
    $stream = Await-WinRT ($sf.OpenAsync([Windows.Storage.FileAccessMode]::Read))
    $decoder = Await-WinRT ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream))
    $bitmap = Await-WinRT ($decoder.GetSoftwareBitmapAsync())
    $result = Await-WinRT ($engine.RecognizeAsync($bitmap))
    $text = $result.Text
    Set-Content -Path (Join-Path $outDir ($f.BaseName + '.txt')) -Value $text -Encoding UTF8
    Write-Host ($f.Name + ' chars=' + $text.Length)
    $stream.Dispose()
  } catch {
    Write-Host ('FAIL ' + $f.Name + ' ' + $_.Exception.Message)
  }
}
Write-Host 'DONE'
