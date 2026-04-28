# ChatGPT Orchestrator MCP Server

Минимальный remote MCP server на Python для схемы:

```text
ChatGPT -> MCP server -> main orchestrator -> helper agents
```

На первом этапе сервер содержит один tool:

- `run_orchestrator`
- вход: `goal: string`
- выход: простой JSON

Внутри сейчас стоит заглушка. Позже ее можно заменить на вызов вашего настоящего главного агента.

## Почему FastMCP

FastMCP выбран потому, что он позволяет описать MCP tool обычной Python-функцией и сразу запустить remote MCP endpoint по HTTP. Для подключения в ChatGPT нужен публичный HTTPS endpoint вида `/mcp`.

## Структура проекта

```text
.
├── .gitignore
├── server.py
├── requirements.txt
├── Procfile
├── render.yaml
└── README.md
```

## Локальный запуск

Требования:

- Python 3.11+
- pip

### 1. Создать виртуальное окружение

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Если на Windows команда `python` открывает Microsoft Store или не показывает версию, используйте:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Запустить сервер

```bash
python server.py
```

Локальный MCP endpoint:

```text
http://localhost:8000/mcp
```

Обычная проверка, что сервер жив:

```text
http://localhost:8000/health
```

Если клиент просит endpoint со слэшем в конце, используйте:

```text
http://localhost:8000/mcp/
```

## Проверка локально

Оставьте `python server.py` запущенным. Во втором терминале выполните:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok"
}
```

Важно: если открыть `http://localhost:8000/mcp` в браузере или дернуть его обычным `curl` без MCP-заголовков, можно увидеть ошибку:

```json
{
  "error": {
    "message": "Not Acceptable: Client must accept text/event-stream"
  }
}
```

Это нормально для MCP endpoint. Проверяйте `/health` обычным браузером, а `/mcp` проверяйте MCP-клиентом.

```powershell
@'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()
        print("TOOLS:")
        for tool in tools:
            print("-", tool.name)

        result = await client.call_tool(
            "run_orchestrator",
            {"goal": "Create an MVP launch plan"}
        )
        print("RESULT:")
        print(result)

asyncio.run(main())
'@ | python
```

Ожидаемый смысл ответа: сервер покажет tool `run_orchestrator` и вернет JSON с текстом, что заглушка приняла задачу.

Можно также проверить через MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

В UI выберите transport `Streamable HTTP` и URL:

```text
http://localhost:8000/mcp
```

## Деплой на Render

### Вариант через GitHub

1. Создайте новый GitHub-репозиторий.
2. Загрузите туда эти файлы.
3. Откройте Render.
4. Нажмите `New` -> `Web Service`.
5. Подключите GitHub-репозиторий.
6. Render обычно сам прочитает `render.yaml`.
7. Если настраиваете вручную:
   - Runtime: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python server.py`
8. Нажмите `Deploy`.

После деплоя Render выдаст URL примерно такого вида:

```text
https://chatgpt-orchestrator-mcp.onrender.com
```

Production MCP endpoint будет:

```text
https://chatgpt-orchestrator-mcp.onrender.com/mcp
```

Production health endpoint для проверки в браузере:

```text
https://chatgpt-orchestrator-mcp.onrender.com/health
```

Именно этот URL нужно вставлять в ChatGPT.

## Как подключить к ChatGPT

1. Откройте ChatGPT в браузере.
2. Перейдите в `Settings`.
3. Откройте `Apps & Connectors` или `Connectors`.
4. Включите Developer Mode, если он еще выключен:
   - `Advanced settings`
   - `Developer mode`
5. Нажмите `Create` или `Create connector`.
6. Заполните:
   - Name: `Orchestrator`
   - Description: `Runs my main orchestrator agent through MCP.`
   - Connector URL: `https://YOUR-RENDER-SERVICE.onrender.com/mcp`
7. Сохраните.
8. В новом чате выберите этот connector/tool и попросите ChatGPT вызвать оркестратор.

## Пример тестового запроса в ChatGPT

```text
Используй Orchestrator и вызови run_orchestrator с goal:
"Составь пошаговый план запуска MVP моего продукта"
```

Ожидаемый ответ от tool сейчас будет примерно:

```json
{
  "status": "ok",
  "message": "Stub orchestrator accepted the goal.",
  "goal": "Составь пошаговый план запуска MVP моего продукта",
  "next_step": "Replace call_real_orchestrator() in server.py with your real agent call."
}
```

## Где заменить заглушку на реального агента

Откройте `server.py` и найдите функцию:

```python
def call_real_orchestrator(goal: str) -> dict[str, Any]:
```

Сейчас она возвращает тестовый JSON. Позже замените ее тело на реальный вызов вашего главного агента.

Пример будущей замены:

```python
def call_real_orchestrator(goal: str) -> dict[str, Any]:
    result = my_main_agent.run(goal)
    return {
        "status": "ok",
        "goal": goal,
        "result": result,
    }
```

Важно: не создавайте отдельный MCP server для каждого подручного агента на первом этапе. Пусть ChatGPT видит только один tool `run_orchestrator`, а уже ваш главный агент внутри решает, каких подручных вызывать.

## Итоговые URL

Локально:

```text
http://localhost:8000/mcp
```

Production URL-шаблон:

```text
https://YOUR-RENDER-SERVICE.onrender.com/mcp
```

URL для ChatGPT:

```text
https://YOUR-RENDER-SERVICE.onrender.com/mcp
```

## Полезные официальные документы

- OpenAI: https://developers.openai.com/apps-sdk/deploy/connect-chatgpt
- OpenAI: https://developers.openai.com/api/docs/mcp
