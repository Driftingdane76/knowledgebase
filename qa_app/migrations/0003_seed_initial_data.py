from django.db import migrations

def seed_data(apps, schema_editor):
    Category = apps.get_model('qa_app', 'Category')
    KnowledgePage = apps.get_model('qa_app', 'KnowledgePage')
    Tag = apps.get_model('qa_app', 'Tag')

    # 1. Categories (Auto-increment integer IDs)
    cat_ejo, _ = Category.objects.get_or_create(name='EJO')
    cat_dag, _ = Category.objects.get_or_create(name='DAG')
    cat_daf, _ = Category.objects.get_or_create(name='DAF')
    cat_boet, _ = Category.objects.get_or_create(name='BOET')

    # 2. Tags (Auto-increment integer IDs)
    tag_names = ['kasko', 'nemkonto', 'mitid', 'crm', 'skade', 'udbetaling', 'godkendelse', 'stenslag', 'fuldmagt', 'dødsbo']
    tags_dict = {t: Tag.objects.get_or_create(name=t)[0] for t in tag_names}

    # 3. 22 Q&A records (No IDs - looked up by title)
    dataset = [
        # --- EJO (Records 1 - 5) ---
        {
            'cat': cat_ejo,
            'title': 'Stenslag dækning på bil AB 12 345',
            'date': '2026-06-01',
            'user': 'Morten N',
            'quest': 'Kunden spørger om stenslag i forruden er dækket uden opkrævning af selvrisiko på EJO-aftaler.',
            'answ': '[hl:green]Ja, reparation af stenslag er dækket med 0 kr. i selvrisiko.[/hl] Hvis ruden skal udskiftes helt, opkræves standard glasselvrisiko på 1.500 kr.',
            'tags': ['stenslag', 'kasko', 'skade']
        },
        {
            'cat': cat_ejo,
            'title': 'Eskalering af låst udbetaling',
            'date': '2026-06-02',
            'user': 'Lars J',
            'quest': 'Udbetalingsflowet hænger med fejlkode EJO-504 ved overførsel af erstatningssum over 50.000 kr.',
            'answ': 'Beløb over 50.000 kr. kræver to-mands godkendelse i EJO-portalen. **Eskaler til teamleder** via intern besked for godkendelse.',
            'tags': ['udbetaling', 'godkendelse']
        },
        {
            'cat': cat_ejo,
            'title': 'Afvist CPR-validering ved oprettelse',
            'date': '2026-06-03',
            'user': 'Sofie P',
            'quest': 'Systemet melder uoverensstemmelse mellem CPR og navn ved nytegning af EJO erhvervsaftale.',
            'answ': 'Tjek om kunden er oprettet med CVR i stedet for personligt CPR. Erhvervspolicer skal oprettes under [hl:yellow]Virksomhedsportalen[/hl].',
            'tags': ['crm', 'mitid']
        },
        {
            'cat': cat_ejo,
            'title': 'Annullering af fejlagtig opkrævning',
            'date': '2026-06-04',
            'user': 'Mette F',
            'quest': 'Kunde er blevet trukket dobbelt for månedlig præmie via Betalingsservice.',
            'answ': 'Opret en modpostering i økonomimoduler under EJO-bogføring. Beløbet refunderes automatisk til kundens [hl:green]NemKonto inden for 2 bankdage[/hl].',
            'tags': ['nemkonto', 'udbetaling']
        },
        {
            'cat': cat_ejo,
            'title': 'Genoptagelse af lukket skadesag',
            'date': '2026-06-05',
            'user': 'Jens H',
            'quest': 'Hvordan genåbner man en EJO-sag, der ved en fejl er markeret som "Afsluttet"?',
            'answ': 'Gå til sagshistorik -> Klik på *Genoptag Sag* -> Vælg årsag [hl:blue]"Supplerende oplysninger modtaget"[/hl].',
            'tags': ['skade']
        },

        # --- DAG (Records 6 - 12) ---
        {
            'cat': cat_dag,
            'title': 'DAG Dagsværksforsikring - Dækningsomfang',
            'date': '2026-06-06',
            'user': 'Camilla N',
            'quest': 'Dækker DAG policen skader på lejet materiel og entreprenørmaskiner?',
            'answ': 'Nej, standard DAG dækker kun **ansvar og personulykke**. Materiel skal tilvælges som særskilt tillægsmodul.',
            'tags': ['kasko', 'skade']
        },
        {
            'cat': cat_dag,
            'title': 'Validering af NemKonto ved DAG erstatning',
            'date': '2026-06-07',
            'user': 'Anders P',
            'quest': 'Kunde ønsker erstatning udbetalt til udenlandsk IBAN-konto i stedet for NemKonto.',
            'answ': 'Udenlandske udbetalinger kræver udfyldt **U-104 formular** samt kopi af pas og bopælsattest i henhold til hvidvaskregler.',
            'tags': ['nemkonto', 'udbetaling']
        },
        {
            'cat': cat_dag,
            'title': 'Fejl i MitID login for DAG erhverv',
            'date': '2026-06-08',
            'user': 'Louise C',
            'quest': 'Kunde får fejlbesked "Bruger ikke autoriseret" ved forsøg på at logge på DAG selvbetjening.',
            'answ': 'Kunden skal have tildelt **Erhvervsfuldmagt i MitID Erhverv** for at kunne tilgå selskabets DAG-policer.',
            'tags': ['mitid', 'crm']
        },
        {
            'cat': cat_dag,
            'title': 'Totalskade vurdering - Bil CD 34 567',
            'date': '2026-06-09',
            'user': 'Henrik L',
            'quest': 'Hvad er reparationsgrænsen for totalskade på erhvervsbiler under DAG?',
            'answ': 'Hvis reparationsomkostningerne overstiger [hl:yellow]75% af handelsværdien[/hl], erklæres køretøjet totalskadet.',
            'tags': ['skade', 'kasko']
        },
        {
            'cat': cat_dag,
            'title': 'Sagsbehandlingstid på DAG anmeldelser',
            'date': '2026-06-10',
            'user': 'Maria K',
            'quest': 'Hvad er standard servicemål for behandling af simple DAG skadesanmeldelser?',
            'answ': 'Simple anmeldelser behandles inden for **3 arbejdsdage**. Kræver sagen taksator, er fristen 7 arbejdsdage.',
            'tags': ['skade']
        },
        {
            'cat': cat_dag,
            'title': 'Ændring af selvrisiko på eksisterende police',
            'date': '2026-06-11',
            'user': 'Morten N',
            'quest': 'Kan kunden hæve sin selvrisiko midt i en policeperiode for at sænke præmien?',
            'answ': 'Ja, ændringen træder i kraft fra d. 1. i den efterfølgende måned. [hl:green]Opret tillægsaftale i CRM.[/hl]',
            'tags': ['crm']
        },
        {
            'cat': cat_dag,
            'title': 'Dækning ved force majeure hændelser',
            'date': '2026-06-12',
            'user': 'Lars J',
            'quest': 'Er oversvømmelse som følge af skybrud dækket under standard DAG bygningsskade?',
            'answ': 'Ja, skybrudsskader er dækket forudsat at nedbørsmængden oversteg **15 mm på 30 minutter** eller 40 mm på 24 timer.',
            'tags': ['skade']
        },

        # --- DAF (Records 13 - 17) ---
        {
            'cat': cat_daf,
            'title': 'DAF Dansk Automobil Forhandler skaderapport',
            'date': '2026-06-13',
            'user': 'Sofie P',
            'quest': 'Forhandler har indsendt skade på prøveplader (prøveskilt). Hvilken selvrisiko gælder?',
            'answ': 'Forhandlerprøveskilte har en fast selvrisiko på [hl:yellow]5.000 kr. pr. skadebegivenhed[/hl] i henhold til DAF-hovedaftalen.',
            'tags': ['kasko', 'skade']
        },
        {
            'cat': cat_daf,
            'title': 'Overførsel af anciennitet ved forhandlerkøb',
            'date': '2026-06-14',
            'user': 'Mette F',
            'quest': 'Kunde køber ny bil hos DAF-forhandler. Hvordan overføres skadefri anciennitet?',
            'answ': 'Indhent bekræftelse fra tidligere forsikringsselskab via [hl:green]Autotaks / DFIM[/hl]. Ancienniteten opdateres automatisk.',
            'tags': ['crm', 'kasko']
        },
        {
            'cat': cat_daf,
            'title': 'Afvisning af dækning pga. manglende service',
            'date': '2026-06-15',
            'user': 'Jens H',
            'quest': 'Kan motorskade afvises hvis kunden ikke har overholdt autoriseret DAF-serviceeftersyn?',
            'answ': 'Kun hvis det kan påvises af taksator, at den manglende vedligeholdelse er den [hl:yellow]direkte årsag til motorskaden[/hl].',
            'tags': ['skade', 'kasko']
        },
        {
            'cat': cat_daf,
            'title': 'Udbetaling af stilstandserstatning',
            'date': '2026-06-16',
            'user': 'Camilla N',
            'quest': 'Kunde har haft bil på værksted i 6 uger pga. reservedelsmangel. Ydes der erstatning for tabt brugsværdi?',
            'answ': 'Hvis kunden har **Udvidet Vejhjælp & Lånebil** som tilvalg, dækkes lånebil i op til 30 dage.',
            'tags': ['udbetaling', 'kasko']
        },
        {
            'cat': cat_daf,
            'title': 'Håndtering af lånebilsaftaler ved DAF værksted',
            'date': '2026-06-17',
            'user': 'Anders P',
            'quest': 'Hvem hæfter for p-bøder og vejskatter pådraget i en DAF lånebil under værkstedsophold?',
            'answ': 'Det gør føreren af lånebilen. Henvis forhandleren til at videresende opkrævningen med [hl:green]underskrevet lånebilsaftale[/hl].',
            'tags': ['godkendelse']
        },

        # --- BOET (Records 18 - 22) ---
        {
            'cat': cat_boet,
            'title': 'Opsigelse af forsikringer ved dødsfald (Boet)',
            'date': '2026-06-18',
            'user': 'Louise C',
            'quest': 'Arving ønsker at opsige afdødes policer. Hvilken dokumentation kræves?',
            'answ': 'Vi skal have tilsendt en kopi af **Skifteretsattesten** samt billede-ID fra bobestyrer eller fuldmagtshaver før policerne kan annulleres.',
            'tags': ['dødsbo', 'skifteretsattest', 'fuldmagt']
        },
        {
            'cat': cat_boet,
            'title': 'Udbetaling af tilgodehavende præmie til Boet',
            'date': '2026-06-19',
            'user': 'Henrik L',
            'quest': 'Afdøde havde indbetalt for meget i præmie. Hvor skal det overskydende beløb udbetales?',
            'answ': 'Beløbet må [hl:yellow]IKKE udbetales til enkeltpersoners NemKonto[/hl]. Det skal overføres direkte til boets dedikerede skiftekonto.',
            'tags': ['dødsbo', 'udbetaling', 'nemkonto']
        },
        {
            'cat': cat_boet,
            'title': 'Opretholdelse af hus- og brandforsikring under bobehandling',
            'date': '2026-06-20',
            'user': 'Maria K',
            'quest': 'Kan arvingerne opsige husforsikringen mens ejendommen er sat til salg af boet?',
            'answ': 'Det frarådes stærkt. Bygnings- og brandforsikring bør **forblive aktiv i boets navn** indtil skødet er tinglyst på ny køber.',
            'tags': ['dødsbo', 'skade']
        },
        {
            'cat': cat_boet,
            'title': 'Fuldmagtsvalidering ved flere arvinger',
            'date': '2026-06-21',
            'user': 'Morten N',
            'quest': 'Der er 3 arvinger i boet, men kun 1 kontakter os for aktindsigt. Hvad gør vi?',
            'answ': 'Vi skal have en [hl:green]Skiftefuldmagt underskrevet af samtlige arvinger[/hl] nævnt på skifteretsattesten før oplysninger må videregives.',
            'tags': ['fuldmagt', 'dødsbo', 'mitid']
        },
        {
            'cat': cat_boet,
            'title': 'Oprettelse af skadesag opstået efter dødsfald',
            'date': '2026-06-22',
            'user': 'Lars J',
            'quest': 'Der er opstået en vandskade i afdødes hus under bobehandlingen. Hvem anmelder skaden?',
            'answ': 'Bobestyrer eller befuldmægtiget arving anmelder skaden under CPR-nummeret med bemærkningen [hl:blue]"Att: Dødsboet"[/hl].',
            'tags': ['skade', 'dødsbo', 'fuldmagt']
        },
    ]

    for item in dataset:
        page, created = KnowledgePage.objects.get_or_create(
            title=item['title'],
            defaults={
                'category': item['cat'],
                'date': item['date'],
                'username': item['user'],
                'question_text': item['quest'],
                'resolution_text': item['answ'],
            }
        )
        if created and item.get('tags'):
            for t_name in item['tags']:
                if t_name in tags_dict:
                    page.tags.add(tags_dict[t_name])

class Migration(migrations.Migration):

    dependencies = [
        ('qa_app', '0002_alter_knowledgepage_id_alter_pageimage_id'),
    ]

    operations = [
        migrations.RunPython(seed_data),
    ]