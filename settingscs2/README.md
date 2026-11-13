# SETTINGSCS2 — site și aplicație Windows

Interfață neagră/roșie pentru preseturi CS2, bibliotecă locală, import `.cfg`, instalare cu backup și lansare prin Steam. Versiunea 0.5 adaugă un updater pentru GitHub Releases.

## Ce este pregătit

- `desktop/`: aplicația Python, interfața și testele.
- `web/`: site-ul static pentru GitHub Pages.
- `packaging/settingscs2.iss`: installer Windows pentru utilizatorul curent.
- `.github/workflows/release.yml`: teste, compilare `.exe`, installer și publicare Release.
- `.github/workflows/site.yml`: publicarea site-ului din `main`.

Codul updaterului a fost testat local cu răspunsuri/download-uri simulate. Compilarea Windows, installerul și actualizarea completă trebuie validate prin prima rulare GitHub Actions și pe un PC Windows. Installerul nu este semnat digital. Nu există încă backend Community, conturi sau sincronizare cloud.

## 1. Creează repository-ul

1. Autentifică-te pe https://github.com ca `xartezz`.
2. Deschide https://github.com/new și pune numele `settingscs2`.
3. Pentru fluxul inclus, alege **Public**: codul și installerul vor fi vizibile tuturor. Updaterul folosește Releases publice, fără parole/token-uri în aplicație. Dacă vrei cod privat, oprește-te aici: distribuția trebuie configurată separat.
4. Creează repository-ul. Poți bifa Add a README file, apoi îl înlocuiești cu cel din pachet.
5. Dezarhivează `settingscs2-github.zip` pe PC. În folderul rezultat trebuie să vezi `desktop`, `web`, `packaging`, `.github` și `README.md`.
6. În repository: **Add file → Upload files**. Trage CONȚINUTUL folderului (nu ZIP-ul și nu folderul exterior). Include `.github` — fără el nu există automatizările.
7. Apasă **Commit changes** pe `main`. În pagina Code trebuie să vezi direct `desktop/`, `web/`, `packaging/`, `.github/`.

Alternativ: după crearea repository-ului, transmite linkul în conversație și acordă integrației GitHub acces la acel repository; codul poate fi încărcat prin integrare.

## 2. Construiește prima aplicație .exe

1. Deschide tabul **Actions**. Activează Actions dacă GitHub îți cere.
2. Alege **Build Windows installer**.
3. Apasă **Run workflow**, alege `main`, scrie `v0.5.0` în câmpul de versiune și confirmă.
4. Așteaptă până când rularea este verde. Nu trebuie să instalezi Python sau compilatoare pe PC pentru acest pas.
5. Workflow-ul creează singur tag-ul și Release-ul, după compilare. NU crea manual un Release public gol înainte.
6. Deschide **Releases → SETTINGSCS2 v0.5.0 → Assets** și descarcă `SettingsCS2-Setup.exe`.
7. Închide versiunile vechi pornite din `START.bat`, rulează installerul și pornește aplicația din scurtătura SETTINGSCS2.
8. Verifică tabul **Setări → Actualizări**. Repository-ul este completat automat din repository-ul care a produs build-ul.
9. Verifică/importă un config, setează căile CS2 și Steam și salvează-le.

Datele existente rămân în `%LOCALAPPDATA%\SettingsCS2\library.sqlite3`. Executabilul se instalează separat în `%LOCALAPPDATA%\Programs\SettingsCS2`. Nu deschide START.bat după trecerea la versiunea instalată: acesta ar porni din nou copia sursă.

Dacă o rulare eșuează, deschide pasul roșu și transmite logul. Nu afirma că installerul a fost creat dacă rularea nu este verde. Codul este pregătit, nu presupune că primul build a fost deja verificat.

## 3. Activează site-ul

1. Repository → **Settings → Pages**.
2. La **Build and deployment → Source**, selectează **GitHub Actions**.
3. Actions → **Deploy website to GitHub Pages → Run workflow** pe `main`.
4. După succes, linkul apare în Settings → Pages. Pentru numele de mai sus, adresa așteptată este `https://xartezz.github.io/settingscs2/`.
5. Modificările ulterioare din `web/`, salvate pe `main`, publică automat site-ul.

Acesta este un site separat de adresa ChatGPT Site existentă. GitHub nu actualizează automat acea adresă veche. Domeniul `settingscs2.ro` nu este înregistrat/conectat de acest pachet. Datele locale din browser sunt separate între domenii.

Butonul de download din site duce la ultimul installer publicat în GitHub Releases. Înainte de prima versiune verde, linkul nu are încă un installer disponibil.

## 4. Publică un update

1. Modifică fișierele din `desktop/` și salvează-le în `main` (Commit changes / Push).
2. Actions → **Build Windows installer → Run workflow**.
3. Introdu o versiune mai mare: `v0.5.1`, apoi `v0.5.2`, etc. Nu reutiliza o versiune deja publicată.
4. Așteaptă rularea verde și verifică installerul în Releases.
5. Pe PC, repornește aplicația sau apasă **Setări → Verifică actualizări**.
6. Apasă **Instalează și repornește**, confirmă și așteaptă. Aplicația descarcă installerul, verifică SHA-256 din API-ul GitHub și pornește instalarea. Verificarea la pornire este automată; instalarea cere un click.
7. După repornire, numărul versiunii trebuie să fie cel nou. Config-urile personale rămân păstrate.

Nu se modifică fișierele CS2 în timpul actualizării aplicației. Aplicarea unui config în joc rămâne o acțiune separată.
Dacă instalarea eșuează după închiderea aplicației, verifică `%LOCALAPPDATA%\SettingsCS2\update-install.log`; installerul rămâne în subfolderul `updates`. Poți descărca și rula manual installerul din Releases.
SHA-256 verifică integritatea download-ului; nu înlocuiește semnarea digitală Windows.

## Dezvoltare locală

Python 3.10+ cu Tkinter. Rulează `desktop/START.bat` pe Windows.
Teste: `python -m unittest discover -s desktop -v`.
Un build de release folosește Python 3.12 și PyInstaller pe runner Windows; versiunea și repository-ul sunt injectate automat în `desktop/release_config.py`.

## Surse tehnice

- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/rest/releases/releases
- https://pyinstaller.org/en/stable/runtime-information.html
- https://jrsoftware.org/ishelp/topic_setupcmdline.htm
