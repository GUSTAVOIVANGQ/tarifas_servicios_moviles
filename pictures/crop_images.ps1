$dir = "c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\pictures"
Copy-Item "$dir\backup\*.png" "$dir\" -Force

Add-Type -AssemblyName System.Drawing
Get-ChildItem -Path $dir -Filter "*.png" | ForEach-Object {
    $srcPath = $_.FullName
    $bmp = New-Object System.Drawing.Bitmap($srcPath)
    $height = $bmp.Height - 48
    if ($height -gt 0) {
        $rect = New-Object System.Drawing.Rectangle(0, 0, $bmp.Width, $height)
        $cropped = $bmp.Clone($rect, $bmp.PixelFormat)
        $bmp.Dispose()
        
        $tmpPath = "$srcPath.tmp"
        $cropped.Save($tmpPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $cropped.Dispose()
        
        Remove-Item $srcPath -Force
        Rename-Item -Path $tmpPath -NewName $_.Name
        Write-Host "Cropped $($_.Name)"
    } else {
        $bmp.Dispose()
    }
}
