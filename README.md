# FormalizaBot MYPE

Agente conversacional especializado en orientación para la formalización de
micro y pequeñas empresas (MYPE) en Tacna, Perú. Proyecto desarrollado para
el curso de Inteligencia Artificial

## Stack
- Python + LangChain
- LLM vía Groq (Llama 3.1)
- RAG sobre normativa de formalización MYPE
- FastAPI

## Pasos Iniciales
- Crear un entorno virtual dentro del proyecto
```
python3 -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```
- Configurar el entorno `settings.json` en `.vscode/settings.json`
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.organizeImports": true
}
```


## Estado del proyecto
🚧 En desarrollo