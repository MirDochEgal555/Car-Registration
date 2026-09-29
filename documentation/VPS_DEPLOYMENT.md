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

In `.env` mindestens Domain, den Pfad zum öffentlichen Client-CA-Zertifikat,
OpenAI-Key sowie SMTP- und Test-E-Mail-Adresse setzen. `CARTECH_CORS_ORIGINS`
muss dieselbe HTTPS-Domain enthalten.

## Zugangsschutz vor dem Livegang

Die Anwendung verwendet mTLS als einzigen Zugangsschutz: Caddy erstellt und
erneuert das öffentliche HTTPS-Zertifikat automatisch und akzeptiert danach
nur Geräte, die ein gültiges, von der privaten CarTech-Client-CA signiertes
Client-Zertifikat vorlegen. Es gibt weder Caddy Basic Auth noch einen
Anwendungs-Login.

Erzeuge die Client-CA und die einzelnen Gerätezertifikate auf einem sicheren
Admin-Rechner, nicht auf dem VPS. Die CA muss separat gesichert werden; ihr
privater Schlüssel darf weder auf den VPS noch ins Repository gelangen. Kopiere
nur das öffentliche CA-Zertifikat nach
`/home/deploy/cartech/secrets/client-ca.pem` und setze diesen Pfad als
`CARTECH_CLIENT_CA_PATH` in `.env`.

Beispiel mit OpenSSL (für jedes Gerät ein eigenes Zertifikat erstellen):

```bash
openssl genrsa -out cartech-client-ca.key 4096
openssl req -x509 -new -key cartech-client-ca.key -sha256 -days 1825 -out cartech-client-ca.pem -subj '/CN=CarTech Device CA'
openssl genrsa -out tablet-01.key 2048
openssl req -new -key tablet-01.key -out tablet-01.csr -subj '/CN=CarTech Tablet 01'
openssl x509 -req -in tablet-01.csr -CA cartech-client-ca.pem -CAkey cartech-client-ca.key -CAcreateserial -out tablet-01.crt -days 365 -sha256
openssl pkcs12 -export -out tablet-01.p12 -inkey tablet-01.key -in tablet-01.crt -certfile cartech-client-ca.pem -name 'CarTech Tablet 01'
```

Das erzeugte `.p12` nur über einen sicheren Weg auf dem vorgesehenen Gerät
installieren und danach die lokale Kopie entfernen. Wegen der Verwaltung von
Client-Zertifikaten schützt die `.p12`-Datei beim Export mit einem einmaligen
lokalen Kennwort; dieses ist kein Anmeldekennwort der Anwendung. Bei Verlust
eines Geräts die Client-CA rotieren, alle verbleibenden Geräte neu ausstellen
und den VPS mit dem neuen öffentlichen CA-Zertifikat aktualisieren.

Caddy beschafft das TLS-Zertifikat automatisch, sobald der DNS-Eintrag auf den
Server zeigt und Port 80/443 erreichbar sind. Prüfen:

```bash
docker compose ps
curl --cert tablet-01.crt --key tablet-01.key --cacert cartech-client-ca.pem -fsS https://cartech.deine-domain.de/api/v1/health
docker compose logs --tail=100
```

Ohne Client-Zertifikat darf der TLS-Handshake nicht erfolgreich sein. Mit einem
gültigen Client-Zertifikat muss die Anwendung direkt ohne Browser- oder
Anwendungs-Passwort erreichbar sein.

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
Transkripte und damit personenbezogene Daten enthalten: Client-Zertifikate und
die Client-CA sicher verwahren, SSH auf bekannte IPs beschränken und Testdaten
nach Ende des Piloten löschen.

## Testübergabe

Erst den Ablauf selbst mit einem anonymisierten Fahrzeug testen. Danach der
Werkstatt ausschließlich die HTTPS-Adresse senden. Auf iPhone/Android kann sie
im Browser über „Zum Home-Bildschirm“ als PWA abgelegt werden.
