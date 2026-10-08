# Stadtbibliothek – Ausleih-API

Eine REST-API für die Ausleihe einer kleinen Stadtbibliothek. Sie verwaltet
Bücher, Mitglieder und Ausleihen, bietet eine Buchsuche mit Paginierung, prüft
die Geschäftsregeln (höchstens drei offene Ausleihen pro Mitglied, Ausleihe nur
bei freiem Exemplar, Rückgabe schließt eine Ausleihe) und schützt alle
schreibenden Zugriffe über einen API-Key. Alle Fehlerantworten haben denselben
JSON-Aufbau.

## Tech-Stack

- **Python 3.12+**
- **FastAPI** (HTTP-Schicht)
- **Pydantic v2** / **pydantic-settings** (Validierung und Konfiguration)
- **SQLAlchemy 2.0** (ORM, SQLite)
- **uvicorn** (Server)
- **pytest** + FastAPI TestClient (Tests)
- **ruff** (Linting/Formatierung)

## Installation

```bash
python -m pip install -r requirements.txt
```

## Starten

```bash
python -m uvicorn app.main:app --port 8000
```

Der Server legt beim Start die SQLite-Datenbank samt Tabellen automatisch an.
Die interaktive API-Dokumentation liegt unter `http://localhost:8000/docs`.

## Umgebungsvariablen

| Variable       | Bedeutung                              | Standard                  |
| -------------- | -------------------------------------- | ------------------------- |
| `DATABASE_URL` | SQLAlchemy-URL der Datenbank           | `sqlite:///./library.db`  |
| `API_KEY`      | Schlüssel für schreibende Zugriffe     | – (Schreibzugriffe gesperrt) |

Ist `API_KEY` nicht gesetzt, wird jeder schreibende Aufruf mit `401` abgewiesen.
Ohne gesetzten Schlüssel läuft der Server trotzdem und alle lesenden Endpunkte
sind erreichbar.

## Tests

```bash
python -m pytest
```

Die Suite läuft gegen eine eigene temporäre Test-Datenbank und berührt die
Produktivdatei nicht.

## Endpunkte

Lesende Endpunkte sind offen. Jeder schreibende Aufruf benötigt den Header
`X-API-Key`; fehlt er oder ist er falsch, antwortet die API mit `401`.

| Methode | Pfad                     | Body         | Antwort                     |
| ------- | ------------------------ | ------------ | --------------------------- |
| GET     | `/health`                | –            | `200 {"status":"ok"}`       |
| POST    | `/books`                 | `BookCreate` | `201 BookRead`              |
| GET     | `/books?q=&limit=&offset=` | –          | `200 Page[BookRead]`        |
| GET     | `/books/{book_id}`       | –            | `200 BookRead`              |
| PUT     | `/books/{book_id}`       | `BookCreate` | `200 BookRead`              |
| PATCH   | `/books/{book_id}`       | `BookUpdate` | `200 BookRead`              |
| DELETE  | `/books/{book_id}`       | –            | `204`                       |
| POST    | `/members`               | `MemberCreate` | `201 MemberRead`          |
| GET     | `/members?limit=&offset=` | –           | `200 Page[MemberRead]`      |
| GET     | `/members/{member_id}`   | –            | `200 MemberRead`            |
| PUT     | `/members/{member_id}`   | `MemberCreate` | `200 MemberRead`          |
| PATCH   | `/members/{member_id}`   | `MemberUpdate` | `200 MemberRead`          |
| DELETE  | `/members/{member_id}`   | –            | `204`                       |
| POST    | `/loans`                 | `LoanCreate` | `201 LoanRead`              |
| GET     | `/loans?limit=&offset=`  | –            | `200 Page[LoanRead]`        |
| GET     | `/loans/overdue?limit=&offset=` | –     | `200 Page[LoanRead]`        |
| GET     | `/loans/{loan_id}`       | –            | `200 LoanRead`              |
| POST    | `/loans/{loan_id}/return` | –           | `200 LoanRead`              |

### Beispiel

```bash
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"title":"Der Steppenwolf","author":"Hermann Hesse","isbn":"978-3-518-36669-1","year":1927,"copies":3}'
```

## Fehlerformat

Jede Nicht-2xx-Antwort hat denselben Aufbau:

```json
{"error": {"code": "validation_error", "message": "Validation failed", "details": [{"field": "year", "message": "Input should be greater than or equal to 1450"}]}}
```

Mögliche Codes: `unauthorized`, `not_found`, `validation_error`,
`duplicate_isbn`, `duplicate_email`, `loan_limit_reached`,
`no_copies_available`, `already_returned`, `referenced_by_loans`,
`not_implemented`.

## Funktionen

- CRUD für Bücher und Mitglieder (inkl. Teil-Update via PATCH)
- Buchsuche über Titel oder Autor (Teilstring, Groß-/Kleinschreibung egal)
- Paginierung mit `limit` und `offset` für alle Listen
- Ausleihen mit 14-tägiger Leihfrist, Rückgabe und Übersichtsliste
- Geschäftsregeln: maximal drei offene Ausleihen pro Mitglied, Ausleihe nur bei
  freiem Exemplar
- API-Key-Schutz für alle schreibenden Zugriffe
- Einheitliches Fehlerformat für Validierung, 401, 404 und 409
- Automatisches Anlegen des Schemas beim Start
