@echo off
echo Criando estrutura do Challenge Roadmap...

:: Criar diretorios
mkdir static\css
mkdir static\js
mkdir static\images
mkdir templates
mkdir challenges
mkdir database

echo Estrutura de pastas criada!
echo.
echo Agora vamos criar os arquivos...
pause

:: Criar requirements.txt
echo Criando requirements.txt...
(
echo Flask==2.3.3
echo Werkzeug==2.3.7
echo Jinja2==3.1.2
) > requirements.txt

echo Arquivos criados com sucesso!
echo.
echo Execute agora: pip install -r requirements.txt
echo E depois: python app.py
pause