$settings = @{
    OLLAMA_KEEP_ALIVE = "-1"
    OLLAMA_MAX_LOADED_MODELS = "1"
    OLLAMA_NUM_PARALLEL = "1"
    OLLAMA_FLASH_ATTENTION = "1"
    OLLAMA_KV_CACHE_TYPE = "q8_0"
    OLLAMA_CONTEXT_LENGTH = "8192"
}

foreach ($setting in $settings.GetEnumerator()) {
    [System.Environment]::SetEnvironmentVariable(
        $setting.Key,
        $setting.Value,
        [System.EnvironmentVariableTarget]::User
    )

    Set-Item `
        -Path "Env:$($setting.Key)" `
        -Value $setting.Value
    
    Write-Host "Set $($setting.Key)=$($setting.Value)"
}

Write-Host ""
Write-Host "Ollama configuration saved."
Write-Host "Fully quit and restart Ollama for the settings to take effect."

