import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

import requests
from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Literal

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parent / ".env")

# Inicializa o servidor FastMCP
mcp = FastMCP("AnkiTools")

ANKI_CONNECT_URL = os.environ.get("ANKI_CONNECT_URL", "http://localhost:8765")
ANKI_DECK = os.environ.get("ANKI_DECK", "Inglês")
ANKI_MODEL = os.environ.get("ANKI_MODEL", "Básico")

AllowedTags = Literal["vocabulario", "expressao", "chunk", "phrasal-verb"]

def invoke_anki(action, **params):
    """Auxiliar para chamar o AnkiConnect."""
    payload = {"action": action, "version": 6, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise Exception(result["error"])
        return result.get("result")
    except requests.exceptions.ConnectionError:
        raise Exception("Anki não está aberto ou AnkiConnect não foi encontrado.")

@mcp.tool()
def sync_anki() -> str:
    """
    Sincroniza o Anki com o AnkiWeb.
    """
    invoke_anki("sync")
    return "Sincronização iniciada com sucesso!"

@mcp.tool()
def add_english_card(
    front: str,
    translation: str,
    explanation: str,
    tags: List[AllowedTags],
    sync: bool = True
) -> str:
    """
    Adiciona um novo card de inglês ao Anki seguindo o padrão do usuário.
    
    Args:
        front: A palavra, frase ou chunk em inglês.
        translation: A tradução para português.
        explanation: Explicação prática e exemplos de uso.
        tags: Lista de tags (vocabulario, chunk, expressao ou phrasal-verb).
        sync: Se True, sincroniza com o AnkiWeb após adicionar.
    """
    # Formatação do verso conforme pedido: Tradução + Quebra de linha vazia + Explicação
    back = f"{translation}<br><br>{explanation.replace('\n', '<br>')}"
    
    note = {
        "deckName": ANKI_DECK,
        "modelName": ANKI_MODEL,
        "fields": {
            "Frente": front,
            "Verso": back
        },
        "tags": tags,
        "options": {
            "allowDuplicate": False
        }
    }
    
    note_id = invoke_anki("addNote", note=note)
    
    result = f"Card adicionado com sucesso! ID: {note_id} | Tags: {', '.join(tags)}"
    if sync:
        invoke_anki("sync")
        result += " | Sincronizado com AnkiWeb."
        
    return result

@mcp.tool()
def search_notes(query: str) -> str:
    """
    Pesquisa por notes no Anki usando a sintaxe de busca do Anki.
    Exemplo: 'deck:Inglês wipe' ou 'Frente:wipe'.
    Retorna os detalhes dos notes encontrados.
    """
    note_ids = invoke_anki("findNotes", query=query)
    if not note_ids:
        return "Nenhum note encontrado."
    
    notes_info = invoke_anki("notesInfo", notes=note_ids)
    
    output = []
    for note in notes_info:
        fields = note.get("fields", {})
        fields_str = "\n".join([f"  {k}: {v.get('value')}" for k, v in fields.items()])
        tags = ", ".join(note.get("tags", []))
        output.append(f"ID: {note['noteId']}\nModel: {note.get('modelName')}\nFields:\n{fields_str}\nTags: {tags}\n{'-'*20}")
    
    return "\n".join(output)

@mcp.tool()
def edit_note(
    note_id: int,
    front: Optional[str] = None,
    translation: Optional[str] = None,
    explanation: Optional[str] = None,
    fields: Optional[dict] = None,
    tags: Optional[List[AllowedTags]] = None,
    sync: bool = True
) -> str:
    """
    Edita um note existente no Anki.
    
    Args:
        note_id: ID do note a ser editado.
        front: Novo conteúdo para o campo 'Frente'.
        translation: Nova tradução (parte superior do campo 'Verso').
        explanation: Nova explicação (parte inferior do campo 'Verso').
        fields: Dicionário opcional de campos para atualização direta.
        tags: Nova lista de tags (vocabulario, chunk, expressao ou phrasal-verb).
        sync: Se True, sincroniza com o AnkiWeb após editar.
    """
    # Busca informações atuais do note
    notes_info = invoke_anki("notesInfo", notes=[note_id])
    if not notes_info:
        return f"Note com ID {note_id} não encontrado."
    
    current_note = notes_info[0]
    current_fields = current_note.get("fields", {})
    
    update_fields = {}
    
    # Se fields genérico foi passado, usa como base
    if fields:
        update_fields.update(fields)
    
    # Atualiza Frente se fornecido
    if front is not None:
        update_fields["Frente"] = front
    
    # Atualiza Verso (padrão translation + explanation) se fornecido
    if translation is not None or explanation is not None:
        current_verso = current_fields.get("Verso", {}).get("value", "")
        
        # Tenta separar tradução e explicação atuais para preservar o que não foi alterado
        if "<br><br>" in current_verso:
            curr_trans, curr_expl = current_verso.split("<br><br>", 1)
            curr_expl = curr_expl.replace("<br>", "\n")
        else:
            curr_trans = current_verso
            curr_expl = ""
            
        final_trans = translation if translation is not None else curr_trans
        final_expl = explanation if explanation is not None else curr_expl
        
        update_fields["Verso"] = f"{final_trans}<br><br>{final_expl.replace('\n', '<br>')}"
    
    # Aplica as mudanças nos campos
    if update_fields:
        invoke_anki("updateNoteFields", note={"id": note_id, "fields": update_fields})
    
    # Atualiza tags se fornecidas
    if tags is not None:
        invoke_anki("updateNoteTags", note=note_id, tags=tags)
    
    result = f"Note {note_id} atualizado com sucesso!"
    if sync:
        invoke_anki("sync")
        result += " | Sincronizado com AnkiWeb."
        
    return result

@mcp.tool()
def delete_note(note_id: int, sync: bool = True) -> str:
    """
    Deleta um note existente no Anki pelo seu ID.
    
    Args:
        note_id: ID do note a ser deletado.
        sync: Se True, sincroniza com o AnkiWeb após deletar.
    """
    invoke_anki("deleteNotes", notes=[note_id])
    
    result = f"Note {note_id} deletado com sucesso!"
    if sync:
        invoke_anki("sync")
        result += " | Sincronizado com AnkiWeb."
        
    return result


if __name__ == "__main__":
    mcp.run()
