# stupidOLAT: Ein Markdows zu HTML Konverter

## Überblick

Dieses Python-Skript konvertiert Markdown-Dateien in ein HTML-Format, das mit dem Learning Management System (LMS) der Hochschule des Autors kompatibel ist. 

## Besonderheiten 

- Die erste Überschriftsebene (`# Titel`) sollte nicht verwendet werden, da sie vom LMS selbst genutzt wird
- Der Titel der Seite wird durch die zweite Überschriftsebene (`## Titel`) definiert
- Die eigentliche Gliederung des Inhalts beginnt ab der dritten Ebene (`### Abschnitt`)
- Spezielle Formatierungen für verschiedene Aufgabentypen (Vorbereitungs-, In-Class- und Nachbereitungsaufgaben)

## Funktionen

- Konvertiert Markdown zu HTML mit LMS-spezifischer Formatierung
- Formatiert Überschriften mit speziellen Schriftarten und Farben
- Wandelt Blockzitate in formatierte Info/Warnung/Erfolg-Boxen um, basierend auf Inhaltsmarkierungen
- Formatiert Code-Blöcke mit passender Darstellung
- Fügt korrekte Formatierung für Bilder hinzu, inklusive Beschriftungsunterstützung
- Wendet Formatierung auf Tabellen an
- Generiert QR-Codes für gruppenspezifische Links, die im JSON-Format definiert sind
- Unterstützt Fußnoten und andere erweiterte Markdown-Funktionen

## Voraussetzungen

- Python 3.x
- Erforderliche Python-Pakete:
  - `argparse`: Verarbeitung von Kommandozeilenargumenten
  - `re`: Operationen mit regulären Ausdrücken
  - `markdown`: Konvertierung von Markdown zu HTML
  - `bs4` (BeautifulSoup4): HTML-Parsing und -Manipulation
  - `qrcode`: QR-Code-Generierung
  - `Pillow`: Bildverarbeitung (wird von qrcode benötigt)

Installation der erforderlichen Pakete mit pip:

```
pip install markdown beautifulsoup4 qrcode Pillow
```

## Verwendung

### Kommandozeilenargumente

```
usage: script.py [-h] (-f DATEI | -i EINGABE_ORDNER) [-o AUSGABE]

Konvertiert Markdown zu LMS-kompatiblem HTML

optional arguments:
  -h, --help            zeigt diese Hilfenachricht an
  -f DATEI, --file DATEI
                        Verarbeitet eine einzelne Markdown-Datei
  -i EINGABE_ORDNER, --input-folder EINGABE_ORDNER
                        Eingabeordner mit zu konvertierenden Markdown-Dateien
  -o AUSGABE, --output AUSGABE
                        Die Ausgabedatei (für den Einzeldateimodus) oder der Ausgabeordner
                        (für den Ordnermodus)
```

### Beispiele

1. Konvertieren einer einzelnen Markdown-Datei:
   ```
   python script.py -f eingabe.md -o ausgabe.html
   ```

2. Konvertieren aller Markdown-Dateien in einem Ordner:
   ```
   python script.py -i markdown_ordner -o html_ordner
   ```

3. Konvertieren aller Markdown-Dateien in einem Ordner (Standard-Ausgabeordner wird erstellt):
   ```
   python script.py -i markdown_ordner
   ```

## Spezielle Markdown-Formatierung

### Überschriften

Überschriften werden mit speziellen Schriftarten und Farben gemäß den LMS-Anforderungen formatiert:

- Überschriftsebene 1 (`#`): Sollte nicht verwendet werden (vom LMS reserviert)
- Überschriftsebene 2 (`##`): Wird als Seitentitel verwendet, Arial Black, #5fac22 (grün), 36pt, fett
- Überschriftsebene 3-6 (`###` bis `######`): Arial Black, #7e8c8d (grau), fett

**Beispiel:**
```markdown
## Titel der Seite im LMS

### Erster Hauptabschnitt

#### Unterabschnitt
```

### Blockzitate (Aufgabenboxen)

Blockzitate werden in unterschiedlich formatierte Boxen umgewandelt, basierend auf spezifischen Markierungen in der ersten Zeile:

- `[class]` oder `[in-class]`: Wird in eine Warnbox umgewandelt (b_warning Klasse), für In-Class-Aufgaben
- `[post]` oder `[after-class]`: Wird in eine Erfolgsbox umgewandelt (b_success Klasse), für Nachbereitungsaufgaben
- `[pre]` oder `[before-class]`: Wird in eine Wichtig-Box umgewandelt (b_important Klasse), für Vorbereitungsaufgaben
- Standard (keine Markierung): Wird in eine Info-Box umgewandelt (b_info Klasse), für allgemeine Informationen

**Beispiel:**
```markdown
> [pre] Diese Aufgabe muss vor dem Kurs erledigt werden.
> Sie wird als wichtige Box formatiert.

> [class] Dies ist eine In-Class-Aufgabe.
> Sie wird als Warnbox formatiert.

> [post] Diese Aufgabe ist nach dem Kurs zu erledigen.
> Sie wird als Erfolgsbox formatiert.

> Dies ist eine allgemeine Information.
> Sie wird als Info-Box formatiert.
```

### Bilder

Bilder werden standardmäßig zentriert und können Beschriftungen enthalten:

```markdown
![Alternativtext](bild.jpg)
Caption: Dies ist die Bildbeschriftung
```

### Gruppenlinks mit QR-Codes

Das Skript kann Tabellen mit QR-Codes für gruppenspezifische Links generieren, die im JSON-Format definiert sind:

```
[group_links]
{
  "Gruppe A": "https://beispiel.de/gruppe-a",
  "Gruppe B": "https://beispiel.de/gruppe-b",
  "Gruppe C": "https://beispiel.de/gruppe-c"
}
```

Dies generiert eine Tabelle mit Gruppennamen, QR-Codes für jeden Link und klickbaren Links.

### Fußnoten

Das Skript unterstützt Fußnoten gemäß der Python-Markdown-Syntax:

```markdown
Hier ist ein Text mit einer Fußnote[^1].

[^1]: Dies ist der Inhalt der Fußnote.
```

Fußnoten werden am Ende des Dokuments gesammelt und mit Links zum Originaltext versehen.

### Code-Blöcke

Code-Blöcke werden mit spezieller Formatierung dargestellt:

````markdown
```python
def beispiel_funktion():
    print("Hallo Welt!")
```
````

## Funktionsübersicht

### Hauptfunktionen

- `process_file(input_file, output_file=None, title=None)`: Verarbeitet eine einzelne Markdown-Datei
- `process_folder(input_folder, output_folder, title=None)`: Verarbeitet alle Markdown-Dateien in einem Ordner

### Hilfsfunktionen

- `convert_markdown_to_html(markdown_text)`: Konvertiert Markdown-Text zu HTML
- `replace_headers(html_content)`: Wendet LMS-Formatierung auf Überschriften an
- `handle_blockquotes(html_content)`: Formatiert Blockzitate basierend auf dem Aufgabentyp
- `handle_code_blocks(html_content)`: Formatiert Code-Blöcke
- `handle_images(html_content)`: Formatiert Bilder und Beschriftungen
- `handle_tables(html_content)`: Formatiert Tabellen
- `handle_group_links_json(html_content)`: Verarbeitet Gruppenlinks mit QR-Codes
- `add_lms_structure(html_content, title)`: Fügt die gesamte Dokumentstruktur hinzu

## Implementierungsdetails

Das Skript funktioniert wie folgt:
1. Lesen des Markdown-Inhalts aus Datei(en)
2. Konvertieren von Markdown zu grundlegendem HTML
3. Parsen des HTML mit BeautifulSoup
4. Anwenden von Transformationen, um den LMS-Formatierungsanforderungen zu entsprechen
5. Schreiben des formatierten HTML in Ausgabedatei(en)

## Hinweise

- Das Skript extrahiert automatisch den Titel aus der ersten Zeile der Markdown-Datei, wenn diese mit `#` beginnt. Beachten Sie jedoch, dass im LMS die zweite Überschriftsebene (`##`) als Titel verwendet werden sollte.
- Für die Ordnerverarbeitung wird ein Standard-Ausgabeordner mit dem Namen "html_output" erstellt, wenn nicht anders angegeben.
- Die QR-Code-Generierung erfordert die Pakete `qrcode` und `Pillow`.
- Verwenden Sie keine H1-Überschriften in Ihren Markdown-Dateien, da diese vom LMS selbst verwendet werden.
