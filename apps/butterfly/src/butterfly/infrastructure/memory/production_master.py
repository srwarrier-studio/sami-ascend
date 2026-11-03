from butterfly.domain.entities.production import WorkCenter
from butterfly.infrastructure.memory.inventory_master import PLANTS

LINES = 3
SHIFTS = ["M", "A", "N"]
SCRAP_REASONS = ["MATERIAL_DEFECT", "MACHINE_SETTING", "OPERATOR_ERROR", "OTHER"]

WORK_CENTERS = [WorkCenter(plant, f"LINE{number}", f"Line {number}", company) for company, plant in PLANTS.items() for number in range(1, LINES + 1)]
