import unittest

from pipeline import gbd

CAUSES = """cause_id,acause,cause_name,level,parent_id,sort_order,most_detailed
409,_ncd,Non-communicable diseases,1,294,97,0
542,_neuro,Neurological disorders,2,409,207,0
554,neuro_neurone,Motor neuron disease,3,542,212,1
972,neuro_headach,Headache disorders,3,542,213,0
547,neuro_migraine,Migraine,4,972,214,1
687,_inj,Injuries,1,294,335,0
696,_unintent,Unintentional injuries,2,687,344,0
697,inj_falls,Falls,3,696,345,1
1029,total_cancer_reporting,Total cancers,1,294,376,1
"""

ICD_CODES = """cause_name,variant,icd10,icd9,cause_id,note
Motor neuron disease,cod,G12-G12.9,335.2,554,
Motor neuron disease,nonfatal,G12-G129,,554,
Headache disorders,nonfatal,G43-G44,,972,
Other digestive diseases (internal),cod,"K57, K58",,,
Garbage Code (GBD Level 1),cod,R99,,,
"NOTE: a footnote row",nonfatal,,,,
"""

EXTRA = [{"cause_id": 547, "cause": "Migraine", "icd10": "G43"}]

LEVEL3 = """cause_id,cause_name,count_combined,count_male
554,Motor neuron disease,1218518.5,600000
972,Headache disorders,45514778.2,1
697,Falls,40000000,1
"""

LEVEL4 = """cause_id,count_combined
547,40880963.7
"""


class GbdTest(unittest.TestCase):
    def test_in_scope_causes_are_most_detailed_diseases(self):
        causes = gbd.causes_in_scope(CAUSES)
        self.assertEqual(sorted(causes), [547, 554])  # not injuries, not the overlapping totals, not parents
        self.assertEqual(causes[554]["name"], "Motor neuron disease")
        self.assertLess(causes[554]["sort"], causes[547]["sort"])
        self.assertEqual(causes[547]["group"], "Non-communicable diseases")

    def test_icd_rows_name_internal_causes_and_add_project_codes(self):
        rows = gbd.icd_rows(ICD_CODES, EXTRA)
        self.assertEqual([(r["cause_id"], r["variant"]) for r in rows],
                         [("554", "cod"), ("554", "nonfatal"), ("972", "nonfatal"), ("1161", "cod"), ("547", "project")])

    def test_codeless_causes_fold_into_their_nearest_parent_with_codes(self):
        causes = gbd.causes_in_scope(CAUSES)
        rows = gbd.icd_rows(ICD_CODES, [])
        self.assertEqual(gbd.groups(CAUSES, rows, causes), {
            972: {"name": "Headache disorders", "sort": 213.0, "group": "Non-communicable diseases",
                  "level": 3, "members": [547]},
        })
        self.assertEqual(gbd.groups(CAUSES, gbd.icd_rows(ICD_CODES, EXTRA), causes), {})

    def test_dalys_from_both_levels(self):
        dalys = gbd.dalys(LEVEL3, LEVEL4)
        self.assertEqual(dalys[554], 1218518.5)
        self.assertEqual(dalys[547], 40880963.7)


if __name__ == "__main__":
    unittest.main()
