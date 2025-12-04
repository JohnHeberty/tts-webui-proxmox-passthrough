"""
Utilities para parsing seguro de Form() parameters com Enums

Este módulo resolve o problema de FastAPI não converter automaticamente
strings para Enums em Form() parameters.

Ref: SPRINTS.md (SPRINT-04)
Bug Fix: Engine Selection Bug (RESULT.md)
"""
from typing import TypeVar, Type, Optional, Callable
from enum import Enum
from fastapi import Form, HTTPException
from functools import wraps

E = TypeVar('E', bound=Enum)


def parse_enum_form(
    enum_class: Type[E],
    default: Optional[E] = None,
    field_name: str = "value",
    allow_none: bool = False,
    case_sensitive: bool = False
) -> Callable[[str], E]:
    """
    Cria parser de Form() para Enums com validação robusta
    
    Uso com FastAPI Depends():
        ```python
        from app.utils.form_parsers import parse_enum_form
        from app.models import TTSEngine
        from fastapi import Depends
        
        @app.post("/endpoint")
        async def my_endpoint(
            engine: TTSEngine = Depends(
                parse_enum_form(TTSEngine, TTSEngine.XTTS, "tts_engine")
            )
        ):
            # engine já é TTSEngine enum
            ...
        ```
    
    Args:
        enum_class: Enum class (ex: TTSEngine)
        default: Valor default (ex: TTSEngine.XTTS)
        field_name: Nome do campo (para error messages)
        allow_none: Se True, aceita None/vazio
        case_sensitive: Se True, compara case-sensitive
    
    Returns:
        Parser function compatível com FastAPI Depends()
    """
    def parser(value: str = Form(default.value if default else None)) -> E:
        # Aceitar None se permitido
        if not value or value == "":
            if allow_none:
                return None
            elif default:
                return default
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field_name}"
                )
        
        # Tentar converter
        try:
            if not case_sensitive:
                # Case-insensitive matching
                value_lower = value.lower()
                for item in enum_class:
                    if item.value.lower() == value_lower:
                        return item
                # Se não encontrou, raise ValueError
                raise ValueError(f"Invalid value: {value}")
            else:
                # Case-sensitive (usa construtor padrão do Enum)
                return enum_class(value)
            
        except ValueError:
            valid_values = [e.value for e in enum_class]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: '{value}'. Must be one of: {valid_values}"
            )
    
    return parser


def validate_enum_string(
    value: str,
    enum_class: Type[E],
    field_name: str = "value",
    case_sensitive: bool = False
) -> E:
    """
    Valida string e converte para Enum
    
    Uso direto (sem Depends):
        ```python
        from app.utils.form_parsers import validate_enum_string
        from app.models import TTSEngine
        
        tts_engine_str = "f5tts"
        tts_engine = validate_enum_string(tts_engine_str, TTSEngine, "tts_engine")
        # tts_engine é TTSEngine.F5TTS
        ```
    
    Args:
        value: String a validar
        enum_class: Enum class
        field_name: Nome do campo (error messages)
        case_sensitive: Se False (default), ignora case
    
    Returns:
        Enum value
    
    Raises:
        HTTPException: Se valor inválido (400)
    """
    if not case_sensitive:
        value_compare = value.lower()
        for item in enum_class:
            if item.value.lower() == value_compare:
                return item
    else:
        try:
            return enum_class(value)
        except ValueError:
            pass
    
    # Valor inválido
    valid_values = [e.value for e in enum_class]
    raise HTTPException(
        status_code=400,
        detail=f"Invalid {field_name}: '{value}'. Must be one of: {valid_values}"
    )


def validate_enum_list(
    values: list[str],
    enum_class: Type[E],
    field_name: str = "values",
    case_sensitive: bool = False,
    allow_duplicates: bool = True
) -> list[E]:
    """
    Valida lista de strings e converte para lista de Enums
    
    Útil para endpoints que aceitam múltiplos valores.
    
    Args:
        values: Lista de strings
        enum_class: Enum class
        field_name: Nome do campo
        case_sensitive: Se False, ignora case
        allow_duplicates: Se False, remove duplicatas
    
    Returns:
        Lista de Enum values
    
    Raises:
        HTTPException: Se algum valor inválido
    """
    result = []
    seen = set()
    
    for value in values:
        enum_value = validate_enum_string(value, enum_class, field_name, case_sensitive)
        
        if not allow_duplicates:
            if enum_value in seen:
                continue
            seen.add(enum_value)
        
        result.append(enum_value)
    
    return result


# Exemplo de uso completo
if __name__ == "__main__":
    # Exemplo de Enum
    from enum import Enum
    
    class ExampleEngine(Enum):
        XTTS = "xtts"
        F5TTS = "f5tts"
        GPT = "gpt"
    
    # Teste 1: validate_enum_string
    print("=== Teste 1: validate_enum_string ===")
    try:
        engine = validate_enum_string("xtts", ExampleEngine, "engine")
        print(f"✅ 'xtts' → {engine} (value={engine.value})")
    except HTTPException as e:
        print(f"❌ Error: {e.detail}")
    
    try:
        engine = validate_enum_string("F5TTS", ExampleEngine, "engine")
        print(f"✅ 'F5TTS' (uppercase) → {engine} (case-insensitive)")
    except HTTPException as e:
        print(f"❌ Error: {e.detail}")
    
    try:
        engine = validate_enum_string("invalid", ExampleEngine, "engine")
        print(f"✅ 'invalid' → {engine}")
    except HTTPException as e:
        print(f"✅ 'invalid' → HTTPException: {e.detail}")
    
    # Teste 2: validate_enum_list
    print("\n=== Teste 2: validate_enum_list ===")
    try:
        engines = validate_enum_list(
            ["xtts", "f5tts", "XTTS"],
            ExampleEngine,
            "engines",
            allow_duplicates=False
        )
        print(f"✅ ['xtts', 'f5tts', 'XTTS'] → {engines} (duplicates removed)")
    except HTTPException as e:
        print(f"❌ Error: {e.detail}")
    
    print("\n✅ All tests passed!")
