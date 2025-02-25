class ULDKnowledgeDB:
    def __init__(self):
        self.kb_index = {
            "uld_odln_frc":       "Operational Damage Limits Notice (ODLN) for Fire Resistant Container",
            "uld_odln_pallet_net":"Operational Damage Limits Notice (ODLN) for Aircraft Pallet Net",
            "uld_odln_pallet":    "Operational Damage Limits Notice (ODLN) for Aircraft Pallet",
            "uld_odln_std_pallet":"Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Pallet",
            "uld_odln_std_fabric":"Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Container (Fabric Door)",
            "uld_odln_std_solid": "Operational Damage Limits Notice (ODLN) for Standard Certified Aircraft Container (Solid Door)",
            "uld_odln_strap":     "Operational Damage Limits Notice (ODLN) for Restraint Strap",
        }

        self.kb_content = {}
        for key in self.kb_index:
            with open(f"./kb/{key}.txt", "r") as f:
                self.kb_content[key] = f.read()

    def get_kb_article(self, kb_name: str) -> str:
        if kb_name not in self.kb_index:
            raise KeyError(f"Unknown knowledge base article: {kb_name}")
        return self.kb_content[kb_name]

if __name__ == "__main__":
    uld_kb = ULDKnowledgeDB()
    print(uld_kb.get_kb_article("uld_odln_pallet"))