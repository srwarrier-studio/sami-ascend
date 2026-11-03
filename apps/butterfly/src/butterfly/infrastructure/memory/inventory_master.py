from butterfly.domain.entities.inventory import MaterialGroup, StorageLocation

GROUPS = [
    MaterialGroup("BOTANIC", "Botanical raw materials"),
    MaterialGroup("PACKING", "Packaging materials"),
    MaterialGroup("EXTRACT", "Herbal extracts"),
    MaterialGroup("DOSAGE", "Finished dosage forms"),
    MaterialGroup("CULTURE", "Cultures and probiotics"),
    MaterialGroup("ACTIVE", "Active ingredients and premixes"),
    MaterialGroup("PROBIOTIC", "Probiotic powders"),
    MaterialGroup("PRECURSOR", "Chemical precursors"),
    MaterialGroup("ESSOIL", "Essential oils"),
    MaterialGroup("AROMA", "Aroma chemicals"),
]

GROUP_OF = {
    "RAW-2001": "BOTANIC", "RAW-2002": "BOTANIC", "RAW-2003": "BOTANIC", "RAW-2004": "BOTANIC", "RAW-2005": "PACKING", "RAW-2006": "PACKING",
    "RM-1001": "EXTRACT", "RM-1002": "EXTRACT", "RM-1003": "EXTRACT", "RM-1004": "EXTRACT", "RM-1005": "DOSAGE", "RM-1006": "DOSAGE",
    "NRAW-2001": "CULTURE", "NRAW-2002": "CULTURE", "NRAW-2003": "CULTURE", "NRAW-2004": "BOTANIC", "NRAW-2005": "ACTIVE", "NRAW-2006": "ACTIVE",
    "NU-1001": "PROBIOTIC", "NU-1002": "PROBIOTIC", "NU-1003": "PROBIOTIC", "NU-1004": "DOSAGE", "NU-1005": "DOSAGE", "NU-1006": "DOSAGE",
    "ORAW-2001": "PRECURSOR", "ORAW-2002": "ESSOIL", "ORAW-2003": "ESSOIL", "ORAW-2004": "ESSOIL", "ORAW-2005": "ESSOIL", "ORAW-2006": "PRECURSOR",
    "OA-1001": "AROMA", "OA-1002": "AROMA", "OA-1003": "AROMA", "OA-1004": "AROMA", "OA-1005": "AROMA", "OA-1006": "AROMA",
}

PLANTS = {"INA1": "1000", "INA2": "2000", "INA3": "3000"}
RAW_STORE = "0001"
FINISHED_STORE = "0002"

LOCATIONS = [
    StorageLocation(plant, code, name, company)
    for company, plant in PLANTS.items()
    for code, name in ((RAW_STORE, "Raw material store"), (FINISHED_STORE, "Finished goods store"))
]
