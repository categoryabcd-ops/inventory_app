@echo off
chcp 65001 >nul
title Настройка системы учёта инвентаря
echo ================================================
echo    АВТОМАТИЧЕСКАЯ НАСТРОЙКА СИСТЕМЫ
echo ================================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  ВНИМАНИЕ: Требуются права администратора!
    echo Для настройки брандмауэра нужно запустить файл от имени администратора.
    echo.
    echo Пожалуйста, нажмите ПКМ на этом файле и выберите "Запуск от имени администратора"
    echo.
    pause
    exit /b 1
)

echo ✅ Права администратора получены
echo.

:: Установка Python модулей
echo 📦 Установка необходимых модулей Python...
pip install flask flask-socketio python-socketio eventlet flask-cors -q
if %errorLevel% equ 0 (
    echo ✅ Модули успешно установлены
) else (
    echo ⚠️  Ошибка при установке модулей, попробуйте python -m pip install...
    python -m pip install flask flask-socketio python-socketio eventlet flask-cors -q
)
echo.

:: Настройка брандмауэра Windows
echo 🔥 Настройка брандмауэра Windows...

:: Удаляем старое правило если существует
netsh advfirewall firewall delete rule name="Inventory System Port 5000" >nul 2>&1

:: Добавляем новое правило для входящих соединений
netsh advfirewall firewall add rule name="Inventory System Port 5000" dir=in action=allow protocol=tcp localport=5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Правило для входящих соединений добавлено
) else (
    echo ⚠️  Не удалось добавить правило для входящих соединений
)

:: Добавляем правило для исходящих соединений
netsh advfirewall firewall add rule name="Inventory System Port 5000 Out" dir=out action=allow protocol=tcp localport=5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Правило для исходящих соединений добавлено
) else (
    echo ⚠️  Не удалось добавить правило для исходящих соединений
)
echo.

:: Получаем IP адрес
echo 📡 Получение сетевой информации...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4" ^| find "192"') do (
    set IP=%%a
    goto :ipfound
)
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set IP=%%a
    goto :ipfound
)
:ipfound
set IP=%IP: =%
echo.

:: Создаем файл с информацией для пользователей
echo 📝 Создание файла с информацией для подключения...
(
echo ================================================
echo    ИНФОРМАЦИЯ ДЛЯ ПОДКЛЮЧЕНИЯ
echo ================================================
echo.
echo Локальный доступ: http://127.0.0.1:5000
echo Доступ с других компьютеров: http://%IP%:5000
echo.
echo ⚠️  Важно:
echo 1. Все компьютеры должны быть в одной сети
echo 2. Используйте этот IP-адрес для подключения
echo 3. При изменении IP-адреса информация обновится
echo.
echo ================================================
) > "IP_ADDRESS_INFO.txt"

echo ✅ Информация сохранена в файл IP_ADDRESS_INFO.txt
echo.

:: Создаем ярлык для быстрого запуска
echo 🔧 Создание ярлыка для запуска...
echo @echo off > "start_server.bat"
echo title Запуск сервера учёта инвентаря >> "start_server.bat"
echo echo ================================================ >> "start_server.bat"
echo echo    ЗАПУСК СИСТЕМЫ УЧЁТА ИНВЕНТАРЯ >> "start_server.bat"
echo echo ================================================ >> "start_server.bat"
echo echo. >> "start_server.bat"
echo echo 🚀 Запуск сервера... >> "start_server.bat"
echo echo. >> "start_server.bat"
echo python app.py >> "start_server.bat"
echo pause >> "start_server.bat"

echo ✅ Создан файл start_server.bat для быстрого запуска
echo.

:: Открываем порт в брандмауэре дополнительно через PowerShell
echo 🔓 Дополнительная настройка брандмауэра...
powershell -Command "New-NetFirewallRule -DisplayName 'Inventory App' -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Any" 2>nul
echo.

echo ================================================
echo ✅ НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!
echo ================================================
echo.
echo 📋 ЧТО БЫЛО СДЕЛАНО:
echo 1. Установлены необходимые Python модули
echo 2. Настроен брандмауэр для порта 5000
echo 3. Создан файл с IP-адресом для подключения
echo 4. Создан скрипт для быстрого запуска
echo.
echo 🚀 ДЛЯ ЗАПУСКА:
echo 1. Закройте это окно
echo 2. Запустите файл start_server.bat
echo 3. На других компьютерах откройте браузер и введите:
echo    http://%IP%:5000
echo.
echo ⚠️  Если другие компьютеры не подключаются:
echo - Проверьте что они в одной сети
echo - Отключите антивирус временно
echo - Проверьте настройки брандмауэра
echo.
pause