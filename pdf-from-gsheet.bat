:: gsheet->json->latex->pdf pipeline

@echo off

:: parameters
set DOCUMENT=%1

:: json-from-gsheet
pushd .\gsheet-to-json\src
.\json-from-gsheet.py --config "../conf/config.yml" --gsheet "%DOCUMENT%"

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd

:: latex-from-json
pushd .\json-to-latex\src
.\latex-from-json.py --config "../conf/config.yml" --json "%DOCUMENT%"

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd

:: latex-from-json
pushd .\out
lualatex %DOCUMENT%.tex --output-format=pdf --interaction=batchmode

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd
