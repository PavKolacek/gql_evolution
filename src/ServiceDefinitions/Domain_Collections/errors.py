"""Slovník chybových kódů (UUID) pro Domain_Collections.

Každý kód je stabilní: nikdy ho nepřepisuj, jen přidávej nové.
ERROR_CODES slouží i jako dokumentace (kód -> popis).
"""

NOT_AUTHENTICATED       = "7c1e5d2a-3b94-4f60-a8d1-92e4b6c0f315"
COLLECTION_NOT_FOUND    = "b3f20a96-5d7e-4c18-9e41-0a6d8f2c7b53"
COLLECTION_NOT_OWNER    = "e08a4d17-92c3-4b6f-a5d0-3f1b7c9e2a68"
ITEM_NOT_FOUND          = "2d95c7e1-a840-4f3b-b162-8e0d4a5f9c37"
ITEM_DUPLICATE_ENTITY   = "91b6e3f4-0c7a-4d25-8f93-c2a1d5e8b074"
ITEM_INVALID_POSITION   = "5a40d8c2-e1b9-4736-a0f5-7d3c9b2e1a86"
ITEM_ENTITY_MISSING     = "c7e91a05-4f28-4b3d-96d1-e5a0b8f3c249"
ENTITY_TYPE_NOT_FOUND   = "f4a2b690-7d35-4e81-b9c0-1a8e6d3f5b72"
ENTITY_TYPE_CYCLE       = "08d3e5a7-c192-4f64-a7b8-d6f0e2c91a35"
ENTITY_TYPE_IN_USE      = "63c8f1d9-2a5e-4b07-8e34-9b1a7c0d5f28"

ERROR_CODES: dict[str, str] = {
    NOT_AUTHENTICATED: "Uživatel není přihlášen (ctx.user je prázdný).",
    COLLECTION_NOT_FOUND: "Kolekce neexistuje.",
    COLLECTION_NOT_OWNER: "Uživatel není vlastníkem kolekce.",
    ITEM_NOT_FOUND: "Položka kolekce neexistuje.",
    ITEM_DUPLICATE_ENTITY: "Tato entita už v kolekci je.",
    ITEM_INVALID_POSITION: "Pozice položky je mimo povolený rozsah.",
    ITEM_ENTITY_MISSING: "Chybí entity_id vkládané entity.",
    ENTITY_TYPE_NOT_FOUND: "Typ entity neexistuje.",
    ENTITY_TYPE_CYCLE: "Změna rodiče by vytvořila cyklus ve stromu typů.",
    ENTITY_TYPE_IN_USE: "Typ entity má potomky nebo je použit v položkách kolekcí.",
}