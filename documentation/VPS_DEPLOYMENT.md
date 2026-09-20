# VPS-Testbetrieb

Diese Anleitung stellt die komplette Anwendung auf einem einzelnen Ubuntu-VPS
bereit: React-PWA und FastAPI unter derselben HTTPS-Adresse, mit einer
persistent gespeicherten Versand-Outbox. Die Datenbank bleibt in einem Docker
Volume und überlebt daher Container-Updates.

## Voraussetzungen

- Hetzner Cloud Server **CX23**, Standort Nürnberg oder Falkenstein, Ubuntu
  24.04; für den MVP genügt diese Größe.
- Eine Domain oder Subdomain, beispielsweise `cartech.deine-domain.de`.
- Ein DNS-A-Record dieser (Sub-)Domain zur öffentlichen IPv4-Adresse des VPS.
- SMTP-Zugang und ein OpenAI-API-Key. Für den Test eine separate Büro-Adresse
  verwenden.

## Server anlegen und absichern

Beim Anlegen einen SSH-Schlüssel hinterlegen und in der Hetzner-Firewall nur
folgende eingehenden Ports erlauben: `22` (nur die eigene IP), `80` und `443`.

Nach dem ersten Login als root:

```bash
apt update && apt upgrade -y
apt install -y git docker.io docker-compose-plugin
systemctl enable --now docker
adduser --disabled-password --gecos '' deploy
usermod -aG docker deploy
```

Danach als `deploy` anmelden. Nicht als root betreiben.

## Anwendung bereitstellen

```bash
git clone https://github.com/mirdochegal555/Car-Registration.git cartech
cd cartech
cp deploy/.env.example .env
nano .env
docker compose up -d --build
```

In `.env` mindestens Domain, OpenAI-Key sowie SMTP- und Test-E-Mail-Adresse
setzen. `CARTECH_CORS_ORIGINS` muss dieselbe HTTPS-Domain enthalten.

## Zugangsschutz vor dem Livegang

Die Testversion hat drei voneinander unabhängige Schichten:

1. Caddy erstellt und erneuert das HTTPS-Zertifikat automatisch.
2. Caddy Basic Auth erscheint im Browser, bevor irgendeine Seite oder API
   erreichbar ist.
3. Danach verlangt die Anwendung einen eigenen Werkstatt-Login. Die Session
   liegt nur als `Secure`, `HttpOnly`, `SameSite=Strict` Cookie vor.

Die mit `deploy/.env.example` erzeugte `.env` enthält für beide Passwörter nur
Platzhalter. Vor `docker compose up` unbedingt eindeutige, lange Passwörter
vergeben, die beiden Hashes wie in der Datei kommentiert erzeugen und einen
zufälligen `CARTECH_APP_AUTH_SESSION_SECRET` setzen. Basic-Auth- und
App-Passwort müssen verschieden sein. Die `.env` bleibt ausschließlich auf dem
VPS und wird weder committed noch versendet.

Caddy beschafft das TLS-Zertifikat automatisch, sobald der DNS-Eintrag auf den
Server zeigt und Port 80/443 erreichbar sind. Prüfen:

```bash
docker compose ps
curl -u werkstatt-gate:DEIN_BASIC_AUTH_PASSWORT -fsS https://cartech.deine-domain.de/api/v1/health
docker compose logs --tail=100
```

Der Browser muss zuerst nach Basic Auth fragen und danach die CarTech-
Anmeldemaske zeigen. Ohne App-Session liefern Geschäftsendpunkte wie
`/api/v1/registrations/validate` den Status `401`.

## Aktualisieren und sichern

```bash
cd ~/cartech
git pull --ff-only
docker compose up -d --build
```

Vor Updates die Versand-Outbox sichern:

```bash
docker compose exec -T api sh -c 'cp /var/lib/cartech/cartech-deliveries.sqlite3 /var/lib/cartech/cartech-deliveries-backup.sqlite3'
```

Zusätzlich in Hetzner wöchentliche Backups aktivieren. Die Outbox kann
Transkripte und damit personenbezogene Daten enthalten: Zugangsdaten nicht
teilen, SSH auf bekannte IPs beschränken und Testdaten nach Ende des Piloten
löschen.

## Testübergabe

Erst den Ablauf selbst mit einem anonymisierten Fahrzeug testen. Danach der
Werkstatt ausschließlich die HTTPS-Adresse senden. Auf iPhone/Android kann sie
im Browser über „Zum Home-Bildschirm“ als PWA abgelegt werden.
