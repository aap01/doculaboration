:: gsheet->json->context->pdf pipeline

@echo off

:: parameters
set DOCUMENT=%1

:: json-from-gsheet
pushd .\gsheet-to-json\src
python json-from-gsheet.py --config "../conf/config.yml" --gsheet "%DOCUMENT%"

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd

:: context-from-json
pushd .\json-to-context\src
python context-from-json.py --config "../conf/config.yml" --json "%DOCUMENT%"

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd

:: context -> pdf
pushd .\out
ptime context --run %DOCUMENT%.context.tex

if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

popd
