### UIdea

- sources
  - each source
    - browser for image files
    - live filename globbing
    - type: train/test/both
    - browser for table files
    - live regex association between filename & table row
      - mapping of table values to own values (names)

- dataset separation
  - keep train/test types, split "both" type
  - x-validation / n-fold value
  - optional random seed


      [split-select]
        - train/validation as defined in source modules
        - split randomly
            - percent OR number for validation
            - random seed
            - repeat training / validation n times 
        - split by expression on attributes (nice to have)

- reduction
  - (maybe not) process modules (resampling, ...)
  - PCA, RF, linear voxels, ...
    - train only / test only / separate for train & test / both at once
  - final data: [num_subjects, feature_size] + attribute mapping


    ImageReductionModule (image(s) in -> n-dim vector out)
      - Linear (single=True)
      - PCA (single=False)
          

- prediction
  - target attribute
  - RVR, SVR, ...
  - polynomial correction


U berpru fung und Optimierung der Alterungsmodelle
◦ Vergleich der Scha tzgenauigkeiten (BrainAGE)
◦ Vergleich verschiedener Modelle und Datensa tze
◦ Maße der modellspezifischen Scha tzgenauigkeiten
Darstellung und Ausgabe der Ergebnisse:
◦ Text- und Tabellenbasiert
◦ Export als CSV