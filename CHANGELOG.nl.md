### Opgelost
- Gebiedskaarten zijn niet langer klikbaar; gebiedsconfiguratie is nu toegankelijk via het menu met drie puntjes op de gebiedskaart (zorgt voor een consistente manier om instellingen te bereiken).

### Chore
- WebSocket client/server-integratie voor apparaatlogboeken is hersteld: de backend registreert nu `smart_heating/subscribe_device_logs`, de frontend voegt automatisch een `id` toe aan WebSocket-commando's en een tijdelijke `console.debug` voor debuggen is verwijderd. Dit maakt het mogelijk dat Global Settings → Device Logs zich abonneert en live apparaatgebeurtenissen ontvangt. (frontend + backend) — Zie PR #87

Opmerking: PR #87 is op 2025-12-20 samengevoegd in `main`; deze vermeldingen zorgen dat de changelog dit reflecteert.

- Veiligheidssensoren: het toevoegen van een nieuwe sensor via de API behoudt nu meerdere geconfigureerde veiligheidsensoren. Voorheen verving het toevoegen een sensor de hele lijst; de API voegt nu één sensor toe of werkt deze bij zonder de andere te verwijderen. (fix)
