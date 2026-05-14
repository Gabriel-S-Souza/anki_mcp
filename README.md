# anki-mcp

Servidor [MCP](https://modelcontextprotocol.io/) em Python que fala com o **Anki** via **AnkiConnect** (HTTP local). Expõe ferramentas para sincronizar, criar, buscar, editar e apagar notes. Por padrão, novos cards vão para o deck **Inglês** com o modelo **Básico** (campos Frente/Verso); isso é configurável por variáveis de ambiente (ver abaixo).

## Requisitos

- Anki aberto com o add-on [AnkiConnect](https://foosoft.net/projects/anki-connect/) (porta padrão `8765`).
- Python 3.

## Instalação

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Opcional: copie `.env.example` para `.env` e edite. Na subida do processo, o `server.py` carrega o arquivo `.env` na pasta do projeto (via `python-dotenv`, listado em `requirements.txt`). Sem esse pacote, só valem variáveis já exportadas no shell ou `env` do cliente MCP.

## Uso

```bash
python server.py
```

Configure o cliente MCP (por exemplo Cursor) para executar esse comando no diretório do projeto (assim o `.env` ao lado de `server.py` é encontrado).

### Variáveis de ambiente (opcional)

| Variável | Padrão | Uso |
|----------|--------|-----|
| `ANKI_CONNECT_URL` | `http://localhost:8765` | URL do AnkiConnect |
| `ANKI_DECK` | `Inglês` | Deck onde `add_english_card` cria o note |
| `ANKI_MODEL` | `Básico` | Nome do tipo de nota no Anki |

No Cursor, defina `env` no JSON do servidor MCP ou use um arquivo `.env` na raiz do repositório (veja `.env.example`).

## Ferramentas expostas

| Ferramenta        | Função                          |
|-------------------|---------------------------------|
| `sync_anki`       | Sincroniza com AnkiWeb          |
| `add_english_card`| Adiciona card (tags + sync opc.)|
| `search_notes`    | Busca com sintaxe do Anki       |
| `edit_note`       | Edita note por ID               |
| `delete_note`     | Remove note por ID              |
