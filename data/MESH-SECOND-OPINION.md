# Second opinion on the MeSH search terms

A blind second opinion, generated 2026-10-29: Claude Haiku 5.5 saw only each GBD cause's name and the search rules (exact `ConditionMeshTerm` match, ORed, MeSH 2025 labels, no symptom or catch-all headings), never `mesh.yaml`, and used no web search. Both lists were run through stage 7's own logic on the same ClinicalTrials.gov data (2026-10-29T09:00:05) and ChEMBL 37. This is a consistency check between two AI models, not an expert review.

**Agree** means the two lists share at least one heading and give the same bar. **Disagree** means they share no heading, or they give a different bar, or Haiku's headings aren't MeSH headings.

- **Agree: 244 of 281 causes**, including 210 of the 242 causes on the map (89.2% of the mapped burden).
- **Disagree: 37**, 32 of them on the map. They fall into three groups, below.

**Owner's decision (2026-10-29):** keep the `mesh.yaml` terms in all three groups and narrow none of the debatable entries. All 281 entries are marked `reviewed: true`.

Each group is sorted by burden, biggest first. Bars show the phase, with the matching trial count in brackets. 'Approved' comes from ChEMBL.

## 1. Haiku's headings aren't MeSH headings (11)

Haiku named headings that don't exist in MeSH, such as 'Hypertensive Heart Disease' and 'Sepsis, Neonatal'. Its version would find no trials, so these aren't real alternatives. The `mesh.yaml` terms stand unless you see a problem with them.

| Cause | Provinces | Share of burden | `mesh.yaml` terms → bar | Haiku terms → bar |
|---|---|---|---|---|
| 498 Hypertensive heart disease | 1 | 1.18% | Hypertension; Hypertrophy, Left Ventricular → Approved (2,372) | — (not MeSH: Hypertensive Heart Disease) → — |
| 383 Neonatal sepsis and other neonatal infections | 12 | 0.94% | Neonatal Sepsis → Phase 3 (46) | — (not MeSH: Sepsis, Neonatal) → — |
| 591 Chronic kidney disease due to hypertension | 2 | 0.39% | Hypertension, Renal; Nephrosclerosis → Phase 3 (4) | — (not MeSH: Hypertensive Nephropathy) → — |
| 1016 Osteoarthritis hand | 1 | 0.27% | Osteoarthritis → Approved (1,822) | — (not MeSH: Osteoarthritis, Hand) → — |
| 651 Digestive congenital anomalies | 49 | 0.25% | Digestive System Abnormalities; Esophageal Atresia; Hirschsprung Disease → Phase 3 (22) | — (not MeSH: Gastrointestinal Abnormalities) → — |
| 365 Other neglected tropical diseases | 53 | 0.21% | Neglected Diseases; Strongyloidiasis; Mycetoma; Yaws → Approved (22) | — (not MeSH: Neglected Tropical Diseases) → — |
| 679 Other sense organ diseases | 369 | 0.12% | Eye Diseases; Ear Diseases → Approved (222) | — (not MeSH: Sense Organ Diseases) → — |
| 1164 Other benign and in situ neoplasms | 8 | 0.09% | Carcinoma in Situ; Meningioma; Hemangioma; Lipoma; Neurofibroma → Approved (194) | — (not MeSH: Neoplasms, Benign) → — |
| 565 Cannabis use disorders | 27 | 0.03% | Marijuana Abuse → Phase 3 (205) | — (not MeSH: Cannabis-Related Disorders) → — |
| 513 Coal workers pneumoconiosis | 1 | 0.00% | Anthracosis → Phase 2 (1) | — (not MeSH: Coal Workers' Pneumoconiosis) → — |
| 388 Iodine deficiency | 0 | 0.00% | Goiter, Endemic → No trial (0) | — (not MeSH: Iodine Deficiency Disease) → — |

## 2. Haiku picked fewer of the same headings, giving a lower bar (20)

Haiku's headings are all in `mesh.yaml` too. The extra `mesh.yaml` headings find more trials or a ChEMBL-approved drug, which raises the bar. Most of the extras are the disease's main form, for example 'Carcinoma, Hepatocellular' for liver cancer, ALS for motor neuron disease, and 'Osteosarcoma' and 'Ewing Sarcoma' for bone cancer.

Debatable ones:
- **639 Other musculoskeletal disorders:** lupus, ankylosing spondylitis and polymyalgia rheumatica are named. They are in this GBD residual, but they alone make it Approved.
- **602 Other urinary diseases:** 'Urinary Incontinence' alone makes it Approved.
- **1011 Soft tissue sarcomas:** 'Sarcoma' is broad and also catches bone sarcomas.
- **674 Hearing loss:** the broad 'Hearing Loss' and 'Hearing Loss, Sensorineural' versus age-related 'Presbycusis' only.

| Cause | Provinces | Share of burden | `mesh.yaml` terms → bar | Haiku terms → bar |
|---|---|---|---|---|
| 674 Age-related and other hearing loss | 18 | 2.21% | Hearing Loss; Presbycusis; Hearing Loss, Sensorineural → Phase 3 (522) | Presbycusis → Phase 2 (25) |
| 639 Other musculoskeletal disorders | 225 | 1.89% | Musculoskeletal Diseases; Lupus Erythematosus, Systemic; Spondylitis, Ankylosing; Polymyalgia Rheumatica → Approved (802) | Musculoskeletal Diseases → Phase 3 (277) |
| 387 Protein-energy malnutrition | 6 | 0.58% | Protein-Energy Malnutrition; Severe Acute Malnutrition → Phase 3 (53) | Protein-Energy Malnutrition → No trial (12) |
| 417 Liver cancer | 6 | 0.57% | Liver Neoplasms; Carcinoma, Hepatocellular → Approved (970) | Liver Neoplasms → Phase 3 (268) |
| 384 Hemolytic disease and other neonatal jaundice | 12 | 0.19% | Jaundice, Neonatal; Erythroblastosis, Fetal → Phase 3 (39) | Erythroblastosis, Fetal → Phase 2 (2) |
| 618 Other hemoglobinopathies and hemolytic anemias | 26 | 0.19% | Anemia, Hemolytic; Hemoglobinopathies → Approved (69) | Hemoglobinopathies → Phase 3 (30) |
| 471 Kidney cancer | 2 | 0.17% | Kidney Neoplasms; Carcinoma, Renal Cell → Approved (605) | Kidney Neoplasms → Phase 3 (202) |
| 369 Maternal hypertensive disorders | 17 | 0.13% | Pre-Eclampsia; Hypertension, Pregnancy-Induced; Eclampsia → Approved (253) | Hypertension, Pregnancy-Induced → Phase 3 (108) |
| 1012 Malignant neoplasm of bone and articular cartilage | 40 | 0.13% | Bone Neoplasms; Osteosarcoma; Sarcoma, Ewing → Approved (219) | Bone Neoplasms → Phase 3 (68) |
| 447 Nasopharynx cancer | 5 | 0.11% | Nasopharyngeal Carcinoma; Nasopharyngeal Neoplasms → Approved (240) | Nasopharyngeal Neoplasms → Phase 3 (50) |
| 1011 Soft tissue and other extraosseous sarcomas | 1 | 0.09% | Sarcoma; Soft Tissue Neoplasms → Approved (583) | Soft Tissue Neoplasms → Phase 2 (8) |
| 602 Other urinary diseases | 36 | 0.09% | Urologic Diseases; Urinary Incontinence → Approved (667) | Urologic Diseases → Phase 3 (77) |
| 659 Fungal skin diseases | 14 | 0.08% | Dermatomycoses; Tinea → Approved (44) | Dermatomycoses → Phase 3 (2) |
| 657 Pyoderma | 36 | 0.07% | Pyoderma; Impetigo → Approved (16) | Pyoderma → Phase 3 (11) |
| 650 Urogenital congenital anomalies | 77 | 0.06% | Urogenital Abnormalities; Hypospadias; Cryptorchidism → Phase 3 (50) | Urogenital Abnormalities → Phase 1 (2) |
| 554 Motor neuron disease | 13 | 0.05% | Motor Neuron Disease; Amyotrophic Lateral Sclerosis → Approved (311) | Motor Neuron Disease → Phase 3 (49) |
| 352 Cysticercosis | 2 | 0.05% | Neurocysticercosis; Cysticercosis → Approved (2) | Cysticercosis → No trial (2) |
| 1010 Other eye cancers | 14 | 0.01% | Eye Neoplasms; Uveal Neoplasms → Approved (13) | Eye Neoplasms → Phase 3 (11) |
| 683 Periodontal diseases | 0 | 0.00% | Periodontal Diseases; Periodontitis → Approved (946) | Periodontal Diseases → Phase 3 (336) |
| 965 Benign and in situ intestinal neoplasms | 2 | 0.00% | Colonic Polyps; Intestinal Polyps → Phase 3 (134) | Intestinal Polyps → No trial (6) |

## 3. Different headings (6)

The two lists share no heading, or their bars differ for another reason.

- **947 XDR tuberculosis:** Haiku used the multidrug-resistant TB heading, which is a different disease.
- **328 URI and 534 gallbladder:** each has one specific list and one broad parent heading, and both give the same bar.

| Cause | Provinces | Share of burden | `mesh.yaml` terms → bar | Haiku terms → bar |
|---|---|---|---|---|
| 534 Gallbladder and biliary diseases | 23 | 0.34% | Gallstones; Cholecystitis; Cholelithiasis → Phase 3 (166) | Gallbladder Diseases; Biliary Tract Diseases → Phase 3 (36) |
| 328 Upper respiratory infections | 15 | 0.26% | Common Cold; Pharyngitis; Sinusitis; Tonsillitis; Laryngitis → Approved (213) | Respiratory Tract Infections → Approved (219) |
| 660 Viral skin diseases | 12 | 0.08% | Warts; Molluscum Contagiosum → Approved (58) | Skin Diseases, Viral → Phase 3 (6) |
| 947 Extensively drug-resistant tuberculosis | 0 | 0.00% | Extensively Drug-Resistant Tuberculosis → Phase 3 (7) | Tuberculosis, Multidrug-Resistant → Approved (35) |
| 1004 Pulmonary Arterial Hypertension | 0 | 0.00% | Pulmonary Arterial Hypertension → Approved (181) | Hypertension, Pulmonary → Approved (220) |
| 1162 Other vision loss | 0 | 0.00% | Vision, Low; Blindness → Phase 3 (92) | Vision Disorders → Phase 3 (104) |

## Agreed (244)

| Cause | Bar | Headings in common |
|---|---|---|
| 493 Ischemic heart disease | Approved (1,566) | Coronary Artery Disease; Myocardial Ischemia |
| 322 Lower respiratory infections | Approved (1,515) | Bronchiolitis; Pneumonia |
| 976 Diabetes mellitus type 2 | Approved (2,896) | Diabetes Mellitus, Type 2 |
| 496 Intracerebral hemorrhage | Phase 3 (158) | Cerebral Hemorrhage |
| 509 Chronic obstructive pulmonary disease | Approved (1,214) | Pulmonary Disease, Chronic Obstructive |
| 630 Low back pain | Phase 3 (930) | Low Back Pain |
| 381 Neonatal preterm birth | Approved (1,248) | Premature Birth |
| 495 Ischemic stroke | Approved (3,381) | Ischemic Stroke |
| 302 Diarrheal diseases | Approved (225) | Diarrhea |
| 571 Anxiety disorders | Approved (3,859) | Anxiety Disorders |
| 382 Neonatal encephalopathy due to birth asphyxia and trauma | Phase 3 (104) | Asphyxia Neonatorum; Hypoxia-Ischemia, Brain |
| 345 Malaria | Approved (300) | Malaria |
| 568 Major depressive disorder | Approved (4,205) | Depressive Disorder, Major |
| 426 Tracheal, bronchus, and lung cancer | Approved (3,084) | Lung Neoplasms |
| 547 Migraine | Approved (496) | Migraine Disorders |
| 521 Cirrhosis and other chronic liver diseases | Approved (1,368) | Liver Cirrhosis; Liver Diseases |
| 543 Alzheimer's disease and other dementias | Approved (1,894) | Alzheimer Disease; Dementia |
| 934 Drug-susceptible tuberculosis | Approved (370) | Tuberculosis, Pulmonary |
| 390 Dietary iron deficiency | Approved (272) | Anemia, Iron-Deficiency |
| 300 HIV/AIDS resulting in other diseases | Approved (1,328) | Acquired Immunodeficiency Syndrome; HIV Infections |
| 1048 COVID-19 | Approved (2,777) | COVID-19 |
| 643 Congenital heart anomalies | Approved (203) | Heart Defects, Congenital |
| 441 Colon and rectum cancer | Approved (2,383) | Colorectal Neoplasms |
| 515 Asthma | Approved (844) | Asthma |
| 429 Breast cancer | Approved (4,001) | Breast Neoplasms |
| 414 Stomach cancer | Approved (806) | Stomach Neoplasms |
| 631 Neck pain | Phase 3 (580) | Neck Pain |
| 560 Alcohol use disorders | Approved (610) | Alcoholism |
| 385 Other neonatal disorders | Phase 3 (54) | Infant, Newborn, Diseases |
| 332 Meningitis | Approved (75) | Meningitis |
| 612 Other gynecological diseases | Approved (82) | Genital Diseases, Female |
| 559 Schizophrenia | Approved (846) | Schizophrenia |
| 593 Chronic kidney disease due to other and unspecified causes | Approved (886) | Renal Insufficiency, Chronic |
| 545 Idiopathic epilepsy | Approved (571) | Epilepsy |
| 492 Rheumatic heart disease | Phase 3 (12) | Rheumatic Heart Disease |
| 411 Esophageal cancer | Approved (455) | Esophageal Neoplasms |
| 432 Cervical cancer | Approved (678) | Uterine Cervical Neoplasms |
| 562 Opioid use disorders | Approved (664) | Opioid-Related Disorders |
| 1015 Osteoarthritis knee | Phase 3 (1,298) | Osteoarthritis, Knee |
| 341 Measles | Approved (18) | Measles |
| 456 Pancreatic cancer | Approved (936) | Pancreatic Neoplasms |
| 507 Other cardiovascular and circulatory diseases | Approved (1,209) | Cardiovascular Diseases |
| 497 Subarachnoid hemorrhage | Phase 3 (141) | Subarachnoid Hemorrhage |
| 977 Atopic dermatitis | Approved (603) | Dermatitis, Atopic |
| 339 Pertussis | Approved (39) | Whooping Cough |
| 684 Edentulism | Phase 3 (107) | Mouth, Edentulous |
| 575 Autism spectrum disorders | Phase 3 (815) | Autism Spectrum Disorder |
| 500 Atrial fibrillation and flutter | Approved (939) | Atrial Fibrillation; Atrial Flutter |
| 408 Other unspecified infectious diseases | Approved (3,436) | Communicable Diseases |
| 944 Other cardiomyopathy | Approved (1,557) | Cardiomyopathies |
| 477 Brain and central nervous system cancer | Approved (1,080) | Brain Neoplasms; Central Nervous System Neoplasms |
| 438 Prostate cancer | Approved (1,792) | Prostatic Neoplasms |
| 569 Dysthymia | Phase 2 (7) | Dysthymic Disorder |
| 609 Premenstrual syndrome | Phase 3 (88) | Premenstrual Syndrome |
| 544 Parkinson's disease | Approved (1,650) | Parkinson Disease |
| 1007 Other non-Hodgkin lymphoma | Approved (1,093) | Lymphoma, Non-Hodgkin |
| 652 Other congenital birth defects | Phase 3 (221) | Congenital Abnormalities |
| 570 Bipolar disorder | Approved (376) | Bipolar Disorder |
| 592 Chronic kidney disease due to glomerulonephritis | Approved (155) | Glomerulonephritis |
| 625 Other endocrine, metabolic, blood, and immune disorders | Approved (465) | Endocrine System Diseases; Metabolic Diseases |
| 1032 Thyroid diseases | Approved (382) | Thyroid Diseases |
| 530 Paralytic ileus and intestinal obstruction | Phase 3 (29) | Intestinal Obstruction |
| 671 Cataract | Approved (404) | Cataract |
| 394 Syphilis | Phase 3 (38) | Syphilis |
| 489 Other malignant neoplasms | Approved (17,989) | Neoplasms |
| 465 Ovarian cancer | Approved (947) | Ovarian Neoplasms |
| 444 Lip and oral cavity cancer | Phase 3 (149) | Lip Neoplasms; Mouth Neoplasms |
| 536 Gastroesophageal reflux disease | Approved (260) | Gastroesophageal Reflux |
| 595 Urinary tract infections and interstitial nephritis | Approved (203) | Nephritis, Interstitial; Urinary Tract Infections |
| 527 Peptic ulcer disease | Approved (66) | Peptic Ulcer |
| 557 Other neurological disorders | Approved (548) | Nervous System Diseases |
| 1000 Near vision loss | Phase 3 (151) | Presbyopia |
| 319 Typhoid fever | Approved (26) | Typhoid Fever |
| 999 Refraction disorders | Phase 3 (490) | Refractive Errors |
| 664 Urticaria | Approved (92) | Urticaria |
| 579 Conduct disorder | Approved (47) | Conduct Disorder |
| 548 Tension-type headache | Phase 3 (39) | Tension-Type Headache |
| 474 Bladder cancer | Approved (565) | Urinary Bladder Neoplasms |
| 516 Interstitial lung disease and pulmonary sarcoidosis | Approved (369) | Lung Diseases, Interstitial; Sarcoidosis, Pulmonary |
| 685 Other oral disorders | Phase 3 (44) | Mouth Diseases |
| 845 Acute lymphoid leukemia | Approved (588) | Precursor Cell Lymphoblastic Leukemia-Lymphoma |
| 615 Sickle cell disorders | Approved (325) | Anemia, Sickle Cell |
| 337 Encephalitis | Phase 3 (36) | Encephalitis |
| 847 Acute myeloid leukemia | Approved (895) | Leukemia, Myeloid, Acute |
| 535 Pancreatitis | Approved (159) | Pancreatitis |
| 642 Neural tube defects | Phase 3 (55) | Neural Tube Defects |
| 453 Gallbladder and biliary tract cancer | Approved (440) | Biliary Tract Neoplasms; Gallbladder Neoplasms |
| 978 Contact dermatitis | Approved (35) | Dermatitis, Contact |
| 520 Other chronic respiratory diseases | Approved (1,718) | Respiratory Tract Diseases |
| 582 Idiopathic developmental intellectual disability | Phase 3 (150) | Intellectual Disability |
| 423 Larynx cancer | Phase 3 (67) | Laryngeal Neoplasms |
| 649 Congenital musculoskeletal and limb anomalies | Phase 3 (28) | Musculoskeletal Abnormalities |
| 1161 Other digestive diseases | Approved (482) | Digestive System Diseases |
| 501 Aortic aneurysm | Phase 3 (122) | Aortic Aneurysm |
| 627 Rheumatoid arthritis | Approved (577) | Arthritis, Rheumatoid |
| 450 Other pharynx cancer | Phase 3 (148) | Pharyngeal Neoplasms |
| 658 Scabies | Approved (22) | Scabies |
| 367 Maternal hemorrhage | Approved (183) | Postpartum Hemorrhage |
| 975 Diabetes mellitus type 1 | Approved (1,093) | Diabetes Mellitus, Type 1 |
| 528 Gastritis and duodenitis | Phase 3 (25) | Duodenitis; Gastritis |
| 435 Uterine cancer | Approved (516) | Uterine Neoplasms; Endometrial Neoplasms |
| 486 Multiple myeloma | Approved (926) | Multiple Myeloma |
| 655 Psoriasis | Approved (404) | Psoriasis |
| 402 Acute hepatitis B | Approved (335) | Hepatitis B |
| 971 Nonalcoholic fatty liver disease including cirrhosis | Approved (612) | Non-alcoholic Fatty Liver Disease |
| 329 Otitis media | Approved (56) | Otitis Media |
| 1160 Other direct maternal disorders | Phase 3 (401) | Pregnancy Complications |
| 645 Down syndrome | Phase 3 (181) | Down Syndrome |
| 531 Inguinal, femoral, and abdominal hernia | Phase 3 (184) | Hernia, Femoral; Hernia, Inguinal; Hernia, Abdominal |
| 597 Benign prostatic hyperplasia | Approved (212) | Prostatic Hyperplasia |
| 648 Other chromosomal abnormalities | Phase 3 (9) | Chromosome Disorders |
| 838 Sickle cell trait | Phase 3 (16) | Sickle Cell Trait |
| 968 Non-rheumatic calcific aortic valve disease | Phase 3 (229) | Aortic Valve Stenosis |
| 503 Endocarditis | Approved (37) | Endocarditis |
| 401 Acute hepatitis A | Approved (667) | Hepatitis A |
| 682 Caries of permanent teeth | Approved (386) | Dental Caries |
| 351 Schistosomiasis | Approved (20) | Schistosomiasis |
| 607 Endometriosis | Approved (250) | Endometriosis |
| 502 Lower extremity peripheral arterial disease | Approved (370) | Peripheral Arterial Disease |
| 459 Malignant skin melanoma | Approved (927) | Melanoma |
| 943 Other leukemia | Approved (1,980) | Leukemia |
| 632 Gout | Approved (110) | Gout |
| 564 Amphetamine use disorders | Phase 2 (5) | Amphetamine-Related Disorders |
| 533 Vascular intestinal disorders | Phase 3 (9) | Mesenteric Ischemia |
| 391 Other nutritional deficiencies | Phase 3 (238) | Deficiency Diseases |
| 368 Maternal sepsis and other maternal infections | Phase 3 (7) | Puerperal Infection |
| 480 Thyroid cancer | Approved (218) | Thyroid Neoplasms |
| 354 Lymphatic filariasis | Phase 3 (9) | Elephantiasis, Filarial |
| 529 Appendicitis | Approved (94) | Appendicitis |
| 563 Cocaine use disorders | Phase 2 (37) | Cocaine-Related Disorders |
| 375 Indirect maternal deaths | Phase 3 (128) | Pregnancy Complications |
| 668 Other skin and subcutaneous diseases | Approved (230) | Skin Diseases |
| 849 Non-melanoma skin cancer (squamous-cell carcinoma) | Approved (1,160) | Carcinoma, Squamous Cell; Skin Neoplasms |
| 995 Maternal abortion and miscarriage | Phase 3 (52) | Abortion, Spontaneous |
| 340 Tetanus | Approved (45) | Tetanus |
| 964 Myelodysplastic, myeloproliferative, and other hematopoietic neoplasms | Approved (599) | Myelodysplastic Syndromes; Myeloproliferative Disorders |
| 1024 Ulcerative colitis | Approved (456) | Colitis, Ulcerative |
| 1014 Osteoarthritis hip | Phase 3 (222) | Osteoarthritis, Hip |
| 484 Hodgkin lymphoma | Approved (172) | Hodgkin Disease |
| 661 Acne vulgaris | Approved (232) | Acne Vulgaris |
| 656 Cellulitis | Approved (29) | Cellulitis |
| 370 Maternal obstructed labor and uterine rupture | Phase 3 (54) | Dystocia; Uterine Rupture |
| 665 Decubitus ulcer | Approved (185) | Pressure Ulcer |
| 389 Vitamin A deficiency | Phase 3 (29) | Vitamin A Deficiency |
| 546 Multiple sclerosis | Approved (1,024) | Multiple Sclerosis |
| 364 Food-borne trematodiases | Approved (10) | Clonorchiasis; Fascioliasis; Opisthorchiasis; Trematode Infections |
| 969 Non-rheumatic degenerative mitral valve disease | Phase 3 (106) | Mitral Valve Insufficiency; Mitral Valve Prolapse |
| 614 Thalassemias | Approved (107) | Thalassemia |
| 596 Urolithiasis | Phase 3 (329) | Urolithiasis |
| 846 Chronic lymphoid leukemia | Approved (345) | Leukemia, Lymphocytic, Chronic, B-Cell |
| 566 Other drug use disorders | Approved (789) | Substance-Related Disorders |
| 355 Onchocerciasis | Approved (16) | Onchocerciasis |
| 359 Rabies | Phase 3 (28) | Rabies |
| 573 Anorexia nervosa | Phase 3 (139) | Anorexia Nervosa |
| 342 Varicella and herpes zoster | Approved (123) | Chickenpox; Herpes Zoster |
| 320 Paratyphoid fever | Phase 1 (1) | Paratyphoid Fever |
| 361 Ascariasis | Phase 3 (4) | Ascariasis |
| 848 Chronic myeloid leukemia | Approved (116) | Leukemia, Myelogenous, Chronic, BCR-ABL Positive |
| 374 Ectopic pregnancy | Phase 3 (15) | Pregnancy, Ectopic |
| 349 Cutaneous and mucocutaneous leishmaniasis | Approved (25) | Leishmaniasis, Mucocutaneous; Leishmaniasis, Cutaneous |
| 670 Glaucoma | Approved (492) | Glaucoma |
| 605 Polycystic ovarian syndrome | Approved (280) | Polycystic Ovary Syndrome |
| 942 Myocarditis | Approved (26) | Myocarditis |
| 606 Female infertility | Approved (196) | Infertility, Female |
| 483 Mesothelioma | Approved (154) | Mesothelioma, Malignant; Mesothelioma |
| 468 Testicular cancer | Approved (91) | Testicular Neoplasms |
| 644 Orofacial clefts | Phase 3 (67) | Cleft Lip; Cleft Palate |
| 616 G6PD deficiency | Phase 3 (10) | Glucosephosphate Dehydrogenase Deficiency |
| 672 Age-related macular degeneration | Approved (282) | Macular Degeneration |
| 376 Late maternal deaths | Phase 3 (149) | Pregnancy Complications |
| 399 Other sexually transmitted infections | Phase 3 (171) | Sexually Transmitted Diseases |
| 363 Hookworm disease | Phase 3 (16) | Hookworm Infections |
| 608 Genital prolapse | Phase 3 (166) | Uterine Prolapse; Pelvic Organ Prolapse |
| 1025 Crohn's disease | Approved (418) | Crohn Disease |
| 1006 Burkitt lymphoma | Phase 3 (160) | Burkitt Lymphoma |
| 979 Seborrhoeic dermatitis | Approved (18) | Dermatitis, Seborrheic |
| 404 Acute hepatitis E | Phase 3 (9) | Hepatitis E |
| 511 Silicosis | Approved (1) | Silicosis |
| 1013 Neuroblastoma and other peripheral nervous cell tumors | Approved (132) | Neuroblastoma |
| 348 Visceral leishmaniasis | Approved (8) | Leishmaniasis, Visceral |
| 338 Diphtheria | Approved (34) | Diphtheria |
| 598 Male infertility | Approved (93) | Infertility, Male |
| 403 Acute hepatitis C | Approved (252) | Hepatitis C |
| 358 Yellow fever | Phase 3 (21) | Yellow Fever |
| 1005 Hepatoblastoma | Phase 3 (33) | Hepatoblastoma |
| 346 Chagas disease | Approved (16) | Chagas Disease |
| 1009 Retinoblastoma | Phase 3 (20) | Retinoblastoma |
| 362 Trichuriasis | Phase 3 (18) | Trichuriasis |
| 397 Trichomoniasis | Approved (16) | Trichomonas Infections; Trichomonas Vaginitis |
| 604 Uterine fibroids | Approved (100) | Leiomyoma |
| 398 Genital herpes | Approved (9) | Herpes Genitalis |
| 395 Chlamydial infection | Phase 3 (35) | Chlamydia Infections |
| 356 Trachoma | Phase 3 (9) | Trachoma |
| 662 Alopecia areata | Approved (272) | Alopecia Areata |
| 663 Pruritus | Approved (178) | Pruritus |
| 353 Cystic echinococcosis | Phase 2 (6) | Echinococcosis |
| 741 Maternal deaths aggravated by HIV/AIDS | Approved (1,333) | Pregnancy Complications, Infectious; HIV Infections |
| 321 Other intestinal infectious diseases | Phase 3 (33) | Gastroenteritis; Intestinal Diseases, Parasitic |
| 350 African trypanosomiasis | Approved (11) | Trypanosomiasis, African |
| 396 Gonococcal infection | Approved (63) | Gonorrhea |
| 514 Other pneumoconiosis | Phase 3 (3) | Pneumoconiosis |
| 512 Asbestosis | No trial (1) | Asbestosis |
| 970 Other non-rheumatic valve diseases | Phase 3 (181) | Heart Valve Diseases |
| 405 Leprosy | Approved (18) | Leprosy |
| 646 Turner syndrome | Approved (17) | Turner Syndrome |
| 647 Klinefelter syndrome | Approved (6) | Klinefelter Syndrome |
| 935 Zika virus | Phase 3 (33) | Zika Virus Infection |
| 843 Ebola | Approved (24) | Hemorrhagic Fever, Ebola |
| 936 Guinea worm disease | No trial (0) | Dracunculiasis |
| 297 Tuberculosis | Approved (370) | Tuberculosis |
| 298 HIV/AIDS | Approved (1,328) | Acquired Immunodeficiency Syndrome; HIV Infections |
| 357 Dengue | Approved (74) | Dengue |
| 418 Liver cancer due to hepatitis B | Approved (970) | Liver Neoplasms |
| 419 Liver cancer due to hepatitis C | Approved (970) | Liver Neoplasms |
| 420 Liver cancer due to alcohol use | Approved (970) | Carcinoma, Hepatocellular; Liver Neoplasms |
| 421 Liver cancer due to other causes | Approved (970) | Carcinoma, Hepatocellular; Liver Neoplasms |
| 522 Chronic hepatitis B including cirrhosis | Approved (206) | Hepatitis B, Chronic |
| 523 Chronic hepatitis C including cirrhosis | Approved (64) | Hepatitis C, Chronic |
| 524 Cirrhosis due to alcohol | Phase 3 (7) | Liver Cirrhosis, Alcoholic |
| 525 Cirrhosis due to other causes | Approved (353) | Liver Cirrhosis |
| 558 Mental disorders | Approved (679) | Mental Disorders |
| 574 Bulimia nervosa | Phase 2 (104) | Bulimia Nervosa |
| 578 Attention-deficit/hyperactivity disorder | Approved (544) | Attention Deficit Disorder with Hyperactivity |
| 585 Other mental disorders | Approved (850) | Mental Disorders |
| 588 Acute glomerulonephritis | Approved (155) | Glomerulonephritis |
| 613 Hemoglobinopathies and hemolytic anemias | Approved (69) | Anemia, Hemolytic; Hemoglobinopathies |
| 640 Other non-communicable diseases | Approved (275) | Chronic Disease |
| 681 Caries of deciduous teeth | Approved (386) | Dental Caries |
| 686 Sudden infant death syndrome | Phase 3 (22) | Sudden Infant Death |
| 837 Thalassemias trait | Approved (107) | Thalassemia |
| 839 G6PD trait | Phase 3 (10) | Glucosephosphate Dehydrogenase Deficiency |
| 850 Non-melanoma skin cancer (basal-cell carcinoma) | Approved (94) | Carcinoma, Basal Cell |
| 938 Alcoholic cardiomyopathy | No trial (0) | Cardiomyopathy, Alcoholic |
| 946 Multidrug-resistant tuberculosis without extensive drug resistance | Approved (35) | Tuberculosis, Multidrug-Resistant |
| 948 HIV/AIDS - Drug-susceptible Tuberculosis | Approved (1,647) | HIV Infections |
| 949 HIV/AIDS - Multidrug-resistant Tuberculosis without extensive drug resistance | Approved (1,360) | HIV Infections; Tuberculosis, Multidrug-Resistant |
| 950 HIV/AIDS - Extensively drug-resistant Tuberculosis | Approved (1,335) | HIV Infections |
| 954 Latent tuberculosis infection | Phase 3 (50) | Latent Tuberculosis |
| 959 Invasive Non-typhoidal Salmonella (iNTS) | Phase 2 (6) | Salmonella Infections |
| 966 Benign and in situ cervical and uterine neoplasms | Phase 3 (84) | Uterine Cervical Dysplasia |
| 996 Liver cancer due to NASH | Approved (970) | Carcinoma, Hepatocellular; Liver Neoplasms |
| 997 Chronic kidney disease due to diabetes mellitus type 1 | Approved (111) | Diabetic Nephropathies |
| 998 Chronic kidney disease due to diabetes mellitus type 2 | Approved (111) | Diabetic Nephropathies |
| 1017 Osteoarthritis other | Approved (1,822) | Osteoarthritis |
