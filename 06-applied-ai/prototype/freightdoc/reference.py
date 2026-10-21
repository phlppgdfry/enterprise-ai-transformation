"""Reference data the pipeline checks against.

Kept in code (not fetched) so that the pilot runs offline and every check is
reproducible. In production these lists come from the TMS master data.
"""

# UN/LOCODEs Wendelkaai actually ships to or from (subset; the real list is
# maintained in the TMS location master).
LOCODES = {
    "BEZEE": "Zeebrugge", "BEANR": "Antwerp", "BEGNE": "Ghent", "NLRTM": "Rotterdam",
    "NLVLI": "Vlissingen", "GBFXT": "Felixstowe", "GBTIL": "Tilbury", "GBPME": "Portsmouth",
    "GBGRK": "Greenock", "GBIMM": "Immingham", "IEDUB": "Dublin", "IEORK": "Cork",
    "ESBIO": "Bilbao", "ESVLC": "Valencia", "PTLIS": "Lisbon", "FRLEH": "Le Havre",
    "DEHAM": "Hamburg", "DEBRV": "Bremerhaven", "SEGOT": "Gothenburg", "FIHEL": "Helsinki",
    "PLGDN": "Gdansk", "ITGOA": "Genoa", "TRMER": "Mersin", "MAPTM": "Tanger Med",
    "USBAL": "Baltimore", "USSAV": "Savannah", "USNYC": "New York", "CNSHA": "Shanghai",
    "CNNGB": "Ningbo", "SGSIN": "Singapore", "KRPUS": "Busan", "INNSA": "Nhava Sheva",
    "BRSSZ": "Santos", "ZADUR": "Durban",
}

# Incoterms 2020.
INCOTERMS = {"EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"}

# ISO 4217 codes accepted by finance for freight invoices.
CURRENCIES = {"EUR", "USD", "GBP", "SEK", "PLN", "CNY", "CHF", "NOK"}

# ISO 6346 letter values: A=10 upwards, skipping multiples of 11.
_LETTER_VALUES = {}
_v = 10
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    if _v % 11 == 0:
        _v += 1
    _LETTER_VALUES[_c] = _v
    _v += 1


def iso6346_check_digit(first10):
    """Check digit for the first 10 characters of a container number."""
    total = 0
    for i, ch in enumerate(first10):
        value = _LETTER_VALUES[ch] if ch.isalpha() else int(ch)
        total += value * (2 ** i)
    return total % 11 % 10


def iso6346_valid(number):
    """True when `number` is a well-formed ISO 6346 container number."""
    if not isinstance(number, str) or len(number) != 11:
        return False
    owner, category, serial, check = number[:3], number[3], number[4:10], number[10]
    if not (owner.isalpha() and owner.isupper() and category in "UJZ"
            and serial.isdigit() and check.isdigit()):
        return False
    return iso6346_check_digit(number[:10]) == int(check)


# Document types and the words that identify them, in the four languages that
# reach the Zeebrugge doc desk (EN, NL, FR, DE).
DOC_TYPES = ("bill_of_lading", "cmr", "commercial_invoice", "packing_list", "delivery_order")

TITLES = {
    "bill_of_lading": ["bill of lading", "connaissement", "cognossement", "konnossement",
                       "sea waybill", "b/l"],
    "cmr": ["cmr", "lettre de voiture", "vrachtbrief", "frachtbrief", "consignment note"],
    "commercial_invoice": ["commercial invoice", "handelsfactuur", "facture commerciale",
                           "handelsrechnung", "invoice"],
    "packing_list": ["packing list", "paklijst", "liste de colisage", "packliste"],
    "delivery_order": ["delivery order", "vrijgave", "bon de livraison", "freistellung",
                       "release order"],
}

# Fields per document type: name -> (parser, required).
FIELDS = {
    "bill_of_lading": {
        "bl_number": ("ref", True), "shipper": ("text", True), "consignee": ("text", True),
        "vessel": ("text", True), "port_of_loading": ("locode", True),
        "port_of_discharge": ("locode", True), "containers": ("containers", True),
        "seal_numbers": ("list", True), "packages": ("int", True),
        "gross_weight_kg": ("weight", True), "issue_date": ("date", True),
    },
    "cmr": {
        "cmr_number": ("ref", True), "sender": ("text", True), "consignee": ("text", True),
        "place_of_taking_over": ("text", True), "place_of_delivery": ("text", True),
        "date_of_taking_over": ("date", True), "vehicle_plate": ("plate", True),
        "packages": ("int", True), "gross_weight_kg": ("weight", True),
    },
    "commercial_invoice": {
        "invoice_number": ("ref", True), "invoice_date": ("date", True),
        "seller": ("text", True), "buyer": ("text", True), "currency": ("currency", True),
        "incoterm": ("incoterm", True), "hs_codes": ("hs_list", True),
        "line_amounts": ("amount_list", True), "total_amount": ("amount", True),
        "packages": ("int", True), "bl_reference": ("ref", False),
    },
    "packing_list": {
        "reference": ("ref", True), "containers": ("containers", True),
        "packages": ("int", True), "gross_weight_kg": ("weight", True),
        "net_weight_kg": ("weight", True), "bl_reference": ("ref", False),
    },
    "delivery_order": {
        "do_number": ("ref", True), "bl_reference": ("ref", True),
        "containers": ("containers", True), "terminal": ("text", True),
        "valid_until": ("date", True), "pickup_reference": ("ref", True),
    },
}

# Label synonyms per field (lower case). The extractor matches the start of a
# line against these; generator and extractor share the list on purpose, the
# same way a real team shares a label glossary with its OCR vendor.
LABELS = {
    "bl_number": ["b/l no", "b/l number", "bl nr", "connaissement nr", "n° connaissement",
                  "b/l-nr"],
    "shipper": ["shipper", "verlader", "expéditeur", "ablader"],
    "consignee": ["consignee", "ontvanger", "destinataire", "empfänger"],
    "vessel": ["vessel", "schip", "navire", "schiff"],
    "port_of_loading": ["port of loading", "laadhaven", "port de chargement", "ladehafen"],
    "port_of_discharge": ["port of discharge", "loshaven", "port de déchargement",
                          "löschhafen"],
    "containers": ["container no", "container nr", "containers", "conteneur", "container-nr"],
    "seal_numbers": ["seal no", "zegel nr", "plomb", "siegel-nr", "seals"],
    "packages": ["no. of packages", "packages", "aantal colli", "colis", "packstücke",
                 "number of packages"],
    "gross_weight_kg": ["gross weight", "brutogewicht", "poids brut", "bruttogewicht"],
    "net_weight_kg": ["net weight", "nettogewicht", "poids net"],
    "issue_date": ["date of issue", "issue date", "datum uitgifte", "date d'émission",
                   "ausstellungsdatum"],
    "cmr_number": ["cmr no", "cmr nr", "cmr number", "n° cmr"],
    "sender": ["sender", "afzender", "expéditeur (1)", "absender"],
    "place_of_taking_over": ["place of taking over", "plaats inontvangstneming",
                             "lieu de prise en charge", "übernahmeort"],
    "place_of_delivery": ["place of delivery", "plaats aflevering", "lieu de livraison",
                          "ablieferungsort"],
    "date_of_taking_over": ["date of taking over", "datum inontvangstneming",
                            "date de prise en charge", "übernahmedatum"],
    "vehicle_plate": ["vehicle registration", "kenteken", "immatriculation", "kennzeichen",
                      "truck plate"],
    "invoice_number": ["invoice no", "invoice number", "factuurnummer", "n° facture",
                       "rechnungsnummer"],
    "invoice_date": ["invoice date", "factuurdatum", "date de facture", "rechnungsdatum"],
    "seller": ["seller", "verkoper", "vendeur", "verkäufer", "exporter"],
    "buyer": ["buyer", "koper", "acheteur", "käufer", "importer"],
    "currency": ["currency", "munt", "devise", "währung"],
    "incoterm": ["incoterm", "incoterms", "leveringsvoorwaarde", "lieferbedingung"],
    "hs_codes": ["hs code", "hs codes", "gn-code", "code sh", "zolltarifnummer"],
    "line_amounts": ["line amounts", "lijnbedragen", "montants des lignes", "positionsbeträge"],
    "total_amount": ["total amount", "totaal", "montant total", "gesamtbetrag", "total"],
    "bl_reference": ["b/l ref", "b/l reference", "ref. connaissement", "bl ref"],
    "reference": ["packing list no", "paklijst nr", "liste n°", "packliste nr"],
    "do_number": ["delivery order no", "do nr", "do number", "n° bon"],
    "terminal": ["terminal", "kaai", "quai"],
    "valid_until": ["valid until", "geldig tot", "valable jusqu'au", "gültig bis"],
    "pickup_reference": ["pickup ref", "pin code", "afhaalreferentie", "référence d'enlèvement"],
}
