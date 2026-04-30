### PRJNA662919

#### ApiCommonPresenters - Add Presenter and create PR

```bash
git -C veupathdb-repos/ApiCommonPresenters status
git -C veupathdb-repos/ApiCommonPresenters add Model/lib/xml/datasetPresenters/FungiDB.xml && git -C veupathdb-repos/ApiCommonPresenters commit -m "Add FungiDB RNA-seq presenter for Fusarium graminearum (PRJNA1393503) dataset.
- Dataset: Wheat head blight transcriptomics
- Organism: Fusarium graminearum (multiple isolates)
- Isolates: PH-1, Lz333, Lz26
- Samples: 12 (4 isolate/condition groups × 3 biological replicates)
- Conditions: PDA medium and 34°C temperature stress
- Added fgra_PRJNA1393503_rnaSeq_RSRC datasetPresenter to FungiDB.xml
- Contact: Sichuan Agricultural University, China"

cd veupathdb-repos/ApiCommonPresenters
gh pr create --title "Add FungiDB presenter for Fusarium graminearum (PRJNA1393503) RNA-seq dataset" --body "Adds RNA-seq presenter for Fusarium graminearum wheat head blight transcriptomics RNA-seq (PRJNA1393503) dataset"
```

#### EbrcModelCommon - Add contact and create PR

```bash
cd -
git -C veupathdb-repos/EbrcModelCommon status
git -C veupathdb-repos/EbrcModelCommon add Model/lib/xml/datasetPresenters/contacts/allContacts.xml && git -C veupathdb-repos/EbrcModelCommon commit -m "Add Tsutomu Arie contact for Fusarium oxysporum (PRJNA662919) RNA-seq dataset.
- Dataset: Morphological differentiation transcriptomics
- PMID: 34108627
- Organism: Fusarium oxysporum isolate Cong:1-1
- Added Tsutomu Arie, arie@cc.tuat.ac.jp, Osaka Prefecture University, Japan"
```
