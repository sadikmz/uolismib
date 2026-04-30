### Data: [**Full species name ** ](links to bioproject ID)

Redmine:  

##### 1. Collect meta-data 

- Organims name: 
- BioProjet:
- GEO:
- Milestone -> Dataset release version:
- Build: 
- Journal article: tmp/BioProjectID_article.pdf
- PMID: 
- Milestone -> Dataset release version:

##### 2. Creating branch

Create Git branch for the for dataset arranged for scheduling under ApiCommonPresenters EbrcModelCommon branches. 

```bash
# build number is indicated in the BBR_dataset_scheling google spreadsheet: https://docs.google.com/spreadsheets/d/14EDheFKLZ5Ahy5CmRtc-zKiR5MmwOxx_8uAcsmlZzpk/edit?usp=sharing
# If is not indicatd, a string "blank" is used.  

cd ~/dataset-curator
build=
datasetRelease=Release-"$build"-datasets
BioProjectAccession=

for repo in ApiCommonDatasets ApiCommonPresenters EbrcModelCommon; do
    git -C veupathdb-repos/$repo switch -c $datasetRelease/$BioProjectAccession
done

for repo in ApiCommonDatasets ApiCommonPresenters EbrcModelCommon; do
  if [ -d "veupathdb-repos/$repo" ]; then
    echo "$repo: $(git -C veupathdb-repos/$repo branch --show-current)"
  fi
done   
```

##### 2. Activate claude skils /curate-bulk-rnaseq  

```bash
# pwd shows ~/dataset-curator
sadik@UoL dataset-curator % pwd 
/Users/sadik/dataset-curator

# Create an addtional terminal (Commad + T in mac OS), login in claude and activate curate-bulk-rnaseq skills in one of the terminal

# In the other terminal created, check whether it shows git was switched the same branch. This terminal is for committing and creating PR after the curation process is completed.  
build=
datasetRelease=Release-"$build"-datasets
BioProjectAccession=
for repo in ApiCommonDatasets ApiCommonPresenters EbrcModelCommon;
do
echo "$repo"
git -C veupathdb-repos/$repo checkout $datasetRelease/$BioProjectAccession
done
```

##### 3. Define task and provide links

- For each dataset, the following detail is filled and some of the list will be excluded say if does not have publication, some other is added (submitting insitution and its abbreviations when there is not publication associated with the dataset).   
- Replace *"$build"* and *BioProjectID* in **Release-"$build"-datasets/BioProjectID** from appropriate detail captured in the meta-data and git branch creation stages

- Description of meta-data and claude prompt details 

  ```bash
  I would like to curate an RNA-seq dataset for FundgiDB. 
  BioProjet: BioProjectID (https://www.ncbi.nlm.nih.gov/bioproject/BioProjectID)
  Organims name: 
  Build number:  
  Article: tmp/BioProjectID_article.pdf 
  Sumitting institute: 
  Check first if Presenter and delivery files this BioProjectID were previously generated in tmp/, delivery/, respectively. If exist, update contents and show updates 
  
  git branch information: Release-"$build"-datasets/BioProjectID
  - Check first curated data / samples in tmp/ and delivery/bulk-rnaseq/BioProjectID/ exist for BioProjectID and curate only new pathogen samples that have not been included in delivery/bulk-rnaseq/BioProjectID/ files
  - Check if the dataset contains mixed reads (single-end and pair-end reads).
  - Check if the dataset is Dual RNA-seq.
  - Check if the dataset is pathogen or host transcriptome and process only pathogen transcriptome unless it is a dual RNA-sequence dataset.
  - Use only pathogen RNA-seq dataset.
  - Report any inconsitency of provided data description vs date parsed before generate presenter and delivery files 
  - If it is a mixed read dataset, process paired-end reads dataset first. 
  - "description" section of datasetPresenter should only describe the data and Methodology used.  
  - If contact person not available, use RNA-seq submitting institution details. 
  
  After generating presenter and delivery files:
  - Read tmp/commit_pr_commands.md and append git commit and pr details it and add GEO number (if available) in the commit message
  - Read tmp/dataset_summary.md and append dataset summary (eg. sample groups details with replication details if any and other associated details) in the same format as in tmp/dataset_summary.md
  - Show contact xml and presente for review before inserting them
  - Generate a descriptive title summarising the dataset (print it to the screen with multiple options to choose from)
  - Generate a "shortDisplayName" for the presenter field: Format - a concatentation of first letter of the species and the secont thre letters of the species name + "_" and four to five letter description capturing the what the experiment is about
  ```

##### 4. Process the data

##### 5. Review output 

- Check Claude generated details 

##### 6. Quality Control Checklist

- manually review each fields of the presenter, make edits as necessary 
- I am using Atom to view and edit the Presenter fields. 
- If any edit issues catched after staging or commit, git will be reset to just before the oldest commit and then emended.   

##### 7. Commit and push come BEFORE the PR

- add, commit, push, PR 

###### commit message

- veupathdb-repos/ApiCommonPresenter	
  - Contents clauded generated git detail editted and final verison will be added here


```bash
# git command here

# links to pr here
```



- veupathdb-repos/EbrcModelCommon
  - Contents clauded generated git detail editted and final verison will be added here


```bash
# git command here

# links to pr here
```



### Additional template files 

- tmp/commit_pr_commands.md:  it is a tempalte git commit details to read and write to and is placed in ~/dataset-curator under *tmp* directory
  - the file contains prevouse commit details for each bioproject dataset 
  - the following is contents for PRJNA662919 dataset 

- tmp/dataset_summary.md
  - the file is placed in ~/dataset-curator under *tmp* directory
  - the following is contents of dataset_summary.md for PRJNA662919 dataset
  - This summary detail is used to exact sample groups information and cross-check the dataset: the summary then get incorporated into [RNA-seq data with sample groups google spreadsheet](https://docs.google.com/spreadsheets/d/1bC-F1k6VX-DGHvNG_VChQsttMY3RPIsOzEOc2LQxbA4/edit?usp=sharing)    

