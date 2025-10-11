@echo off
echo ========================================================
echo      LIMPAR CACHE PYTHON E INICIAR - EviChain
echo ========================================================
echo.

echo PROBLEMA IDENTIFICADO:
echo O codigo esta correto, mas o Python esta usando cache antigo!
echo.

echo Passo 1: Parando qualquer servidor rodando...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo OK
echo.

echo Passo 2: Limpando cache Python (__pycache__)...
if exist "__pycache__" (
    rmdir /S /Q "__pycache__"
    echo OK - __pycache__ removido
) else (
    echo OK - __pycache__ nao existe
)
echo.

echo Passo 3: Removendo arquivos .pyc...
del /S /Q *.pyc 2>nul
echo OK
echo.

echo Passo 4: Limpando cache do pip...
pip cache purge >nul 2>&1
echo OK
echo.

echo Passo 5: Verificando versao do OpenAI...
python -c "import openai; print('OpenAI:', openai.__version__)"
echo.

echo Passo 6: Iniciando servidor SEM cache...
echo.
echo ========================================================
echo          INICIANDO EVICHAIN (SEM CACHE)
echo ========================================================
echo.
echo NAO FECHE esta janela enquanto usar o EviChain
echo.
echo Voce deve ver:
echo   [INFO] IA OpenAI inicializada com sucesso
echo.
echo Se ainda aparecer erro de 'proxies', execute:
echo   pip install --force-reinstall openai
echo.
echo ========================================================
echo.

python -B api_server.py

echo.
echo ========================================================
echo           SERVIDOR ENCERRADO
echo ========================================================
echo.
pause

