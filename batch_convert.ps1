param(
    [Parameter(Mandatory = $false)]
    [string]$extension = ".ipynb",

    [Parameter(Mandatory = $false)]
    [string]$token = "_"
    )

$files = Get-ChildItem -Path . -Filter "*$extension"

$filteredFiles = $files | Where-Object {$_.Name.StartsWith($token)}

Write-Output $filteredFiles

$filesCopied = 0
$time = Measure-Command {
    $filteredFiles | ForEach-Object -Parallel {

        $newFileName = $_.BaseName -replace ("^"+$using:token), ""
        $newFilePath = ( $newFileName + '.qmd' )        
        quarto convert $_.FullName --output $newFilePath
 
    }
| Out-Default
} 

$text = "Convertiti $($filteredFiles.Length) file in $($time.TotalSeconds) secondi"

Write-Host (
    "
    {0}
    {1}
    {0}
    " -f ("-"*$text.Length) , $text
)
