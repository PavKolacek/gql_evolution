# Deníček projektu – Uživatelské kolekce (`gql_metadata/Collections`)

**Autoři:** Pavlis Lukáš a Haluzová Nikola

Tento dokument je deník celého průběhu vývoje projektu od prvního commitu až po stav před závěrečnou obhajobou. Zachycuje časovou posloupnost commitů, problémy, které jsme si definovali k vyřešení, co jsme při tom objevili, a hlavně které problémy se dlouho nedařilo řešit a jak byly nakonec vyřešeny.

## Definice problému – co má aplikace umět

Tématem projektu je systém uživatelských kolekcí, do kterých lze ukládat libovolné entity informačního systému (například projekty, grantové výzvy nebo dokumenty). Zadání jsme si na začátku semestru definovali takto:

* `CollectionGQLModel` (kolekce) = pojmenovaná kolekce uživatele, například „Oblíbené", „Projekty k projednání", „Dokumenty k přečtení" nebo „Zajímavé grantové výzvy". Má název (`name`), popis (`description`), vlastníka (`owner_id`) a barvu (`color`).
* `CollectionItemGQLModel` (položka kolekce) = jedna vložená entita. Odkazuje na kolekci (`collection_id`), na vloženou entitu (`entity_id`) a její typ (`entity_type_id`), má svého vlastníka (`owner_id`) a pořadí v kolekci (`position`).
* Jedna kolekce může obsahovat entity různých typů, například kolekce „Oblíbené" může obsahovat 1. Project A, 2. Grant B, 3. Document C.
* Odkaz na vloženou entitu je polymorfní: dvojice `entity_id` + `entity_type_id` místo klasického cizího klíče.
* Z hlediska editace musím být schopen kolekci vytvořit, upravit a smazat a v ní položky přidávat, odebírat a řadit.
* Důležité: kolekce jen odkazuje na entity, nekopíruje je. Položka kolekce není vložená entita samotná.

Z toho vyplynuly hlavní problémy k vyřešení:

1. Vytvořit databázové modely `Collection` a `CollectionItem` a číselník typů entit implementovaný jako strom (typy typů).
2. Umožnit vytváření, úpravu a mazání kolekcí pomocí GraphQL mutací.
3. Umožnit přidávat a odebírat položky kolekce.
4. Umožnit řadit položky v kolekci (udržovat správně `position` při vkládání, odebírání a přesunu).
5. Rozhodnout, jak ošetřit polymorfní referenci (ověřovat existenci vložené entity, nebo ne).
6. Vyřešit autorizaci: kdo smí kolekci číst a měnit a jak naložit s `owner_id` u položky.


Architektura

Dodržujeme architekturu ze vzorového gql_evolution (větev 2026):

GQLTyp / resolver  ->  Service  ->  Loader  ->  DBModel

Resolver nikdy nesahá přímo do databáze, vždy jde přes službu a loader. Struktura src/ odpovídá vzoru (Modely / Loadery / Services / GQLModely).

Technologie: Python 3.11+, strawberry-graphql (+ federation), uvicorn (ASGI), SQLAlchemy 2.x, DataLoaders, Docker / Docker Compose.

# Deníček:

## 16.10.2026 — Add Collection and CollectionItem models to Domain_Collections
* Definice problému: Potřeba přidaní datových modelů.
* Objeveno: -
* Nevyřešené problémy: Potřeba přidání číselníku pro EntityTypeModel.
* Vyřešené problémy: Založení potřebných datových modelů.

## 22.10.2026 — Oprava relací (init=False) a seed: FK se už nepřepisují na NULL

* **Definice problému:** Po vytvoření databázové vrstvy (1. PD) jsme chtěli ověřit, že aplikace běží nad skutečným Postgresem, že se naimportují demodata ze `systemdata.json` a že funguje CRUD nad `Collection` a `CollectionItem`. Cílem bylo mít databázovou vrstvu ověřenou před odevzdáním.

* **Objeveno:**
  * **Seed padal na `A transaction is already begun on this Session`.** Funkce `ImportModels` z `uoishelpers` (`feeders.py`) při každém volání `session_maker()` očekává novou session: nejprve přes ni načte existující řádky a pak otevře transakci. Původní `seed.py` ale pokaždé vracel jednu a tutéž session. Chyba se dosud neprojevila, protože tabulky událostí mají v `systemdata.json` prázdná pole a ukládání se nikdy nespustilo. Naše typy entit jsou první tabulka s daty.
  * **Cizí klíče se při zápisu ukládaly jako `NULL`.** Po úspěšném importu měly všechny položky kolekcí `collection_id` i `entity_type_id` prázdné, a stejně dopadl i `parent_id` u typů entit, takže číselník nebyl strom. Příčinu jsme dohledali pomocí malého skriptu s `echo=True`, který vypsal SQL `INSERT`: konstruktor modelu hodnoty držel (ověřeno přímo v Pythonu), ale v parametrech zápisu už byly `None`.
  * Příčinou byly relace typu „mnoho na jedna" (`CollectionItemModel.collection`, `CollectionItemModel.entity_type`, `EntityTypeModel.parent`) deklarované s `default=None`. Protože jsou modely dataclassy, konstruktor ke každé relaci dosadí `None` a SQLAlchemy to při zápisu vyhodnotí jako „relace je prázdná" a přepíše odpovídající cizí klíč na `NULL`.

* **Nevyřešené problémy:**
  * Zadání pracuje s `owner_id`, naše modely zatím používají `user_id` (podle něj jsou vytvořená i demodata). Přejmenování se musí provést současně v modelech a v `systemdata.json`.
  * Neověřili jsme, co přesně se stane s položkami při smazání kolekce (relace `items` má jen `cascade="save-update"`, tedy bez mazání). Rozhodneme to ve vrstvě služeb.
  * Code coverage je zatím 53 %, protože služby a GQL typy pro kolekce ještě neexistují (2. a 3. PD). Cíl je 95 %.

* **Vyřešené problémy:**
  * **Relace:** v relacích typu „mnoho na jedna" jsme nahradili `default=None` parametrem `init=False`. Konstruktor je tak vůbec nenastavuje a cizí klíče zůstanou zachované. Relace typu „jedna na mnoho" (`items`, `children`) s `default_factory=list` jsme nechali, prázdný seznam klíč nemaže.
  * **Seed:** v `seed.py` jsme původní řešení (sdílená session) zakomentovali a nahradili ho `async_sessionmaker(session.bind, ...)`, takže každé volání dostane novou session. Tabulky se navíc importují v pořadí podle cizích klíčů (`sorted_tables`), aby typy a kolekce byly dřív než položky.
  * **Data:** demodata jsme z databáze smazali (`DELETE FROM collection_items; DELETE FROM entity_types;`) a naimportovali znovu.

* **Ověření:**
  * Automatické testy `pytest tests/db -v`: 3 passed.
  * Ruční CRUD přes CLI (`python -m src.DBDefinitions.main Collection create/get/list/update/delete`) včetně kontroly výsledku v pgAdminu.
  * Zápis položky kolekce jsme zkontrolovali skriptem s vypsaným SQL (`INSERT` už obsahuje vyplněné `collection_id` a `entity_type_id`) a v pgAdminu: 5 typů entit, 4 kolekce a 10 položek, bez `NULL` v cizích klíčích.
