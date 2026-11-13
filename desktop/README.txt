SETTINGSCS2 DESKTOP v0.5 — ALPHA
Windows 10/11, Python 3.10+ cu Tkinter. START.bat incearca py, apoi python.
Daca niciuna dintre comenzi nu este disponibila, instaleaza Python de la
https://www.python.org/downloads/windows/ si activeaza Add Python to PATH
daca optiunea este disponibila. Include componenta Tcl/Tk si IDLE.
Inchide fereastra de eroare si redeschide START.bat dupa instalare.

1. Dezarhiveaza intr-un folder permanent.
2. Ruleaza START.bat. Prima pornire inregistreaza settingscs2:// in HKCU pentru utilizatorul curent; nu necesita admin.
3. Alege folderul Counter-Strike Global Offensive (contine game/bin/win64/cs2.exe) si Steam.exe.
4. Importa un .cfg sau foloseste Add to app pe site, apoi Deschide in aplicatie.
5. Verifica textul config-ului. Inchide CS2. Apasa Aplica sau Aplica si porneste CS2.

Biblioteca persista in %LOCALAPPDATA%\SettingsCS2\library.sqlite3.
Fiecare preset primeste un UUID si un fisier settingscs2_<uuid>.cfg.
La suprascriere, versiunea precedenta este salvata ca .bak in acelasi folder.
Nu se modifica autoexec.cfg, config-urile personale sau launch options persistente din Steam.
Steam este pornit cu argumentele -applaunch 730 +exec settingscs2_<uuid>.cfg, fara shell.
Daca jocul este deja pornit, argumentele de lansare pot sa nu fie aplicate.
Backup-ul acopera doar fisierul dedicat, nu toate setarile schimbate de executia in joc.
DPI, rezolutia si driverele se configureaza manual. Importa numai config-uri pe care le-ai verificat.
Add to app transfera direct continutul config-ului; nu exista sincronizare cloud.
Pentru config-uri mari foloseste descarcarea .cfg si importul manual.

Dezinstalare: sterge cheia HKCU\Software\Classes\settingscs2 folosind regedit,
apoi folderul aplicatiei. Datele locale si config-urile instalate se pot sterge separat.

Verificare: operatiile de validare, scriere, backup si argumentele de lansare au teste automate.
Integrarea Windows, protocolul, Steam si executia efectiva in CS2 nu au fost testate pe un PC Windows in aceasta sesiune.

INTERFATA v0.2
- Jucatori pro: catalog offline cu cautare, detalii, sursa si adaugare in biblioteca.
- Community: setup-uri locale cu nickname, mouse, tastatura, descriere si .cfg.
- Config-urile mele: cautare, previzualizare, editare, export, stergere si aplicare.
- Setari: configurarea si verificarea folderului CS2 si Steam.exe.
Biblioteca existenta este pastrata. Descarca arhiva, dezarhiveaza intr-un folder
permanent si ruleaza START.bat. Deschide Setari si apasa Verifica si salveaza.
Nu sunt necesare pachete pip suplimentare. Python 3.10+ cu Tkinter ramane necesar.
Catalogul pro este un snapshot din 12.11.2026, nu se actualizeaza automat.
Community din aplicatie si Community din browser sunt stocari locale separate.

NAVIGARE v0.3
Detaliile jucatorilor, config-urile, editorul si formularul Community sunt
pagini in fereastra principala. Butonul Inapoi, Alt+Stanga sau Escape revin
la pagina precedenta. Salveaza editarile inainte de a parasi editorul.
Bara de titlu v0.4 este desenata de aplicatie, independent de tema Windows.
Butoane: minimizare, maximizare/restaurare, inchidere. Trage de bara pentru
a muta fereastra; dublu click pentru maximizare. Marginile permit redimensionare.
Maximizarea respecta zona de lucru a monitorului. Alt+F4 inchide aplicatia.
Selectarea fisierelor si confirmarile folosesc in continuare dialoguri Windows.
Controalele ferestrei necesita verificare interactiva pe Windows.

ACTUALIZARI v0.5
In Setari, configureaza repository-ul public de incredere ca utilizator/repository.
Verificarea ruleaza la pornire; instalarea cere confirmare. GitHub Actions creeaza
installerul Windows. Vezi README.md din pachetul complet pentru pasii de configurare.
