# Modules

 Let's suppose we want to have several source directories

    source_directory    | glob_pattern              | object_sub_path
    /datasets/set1        *.nii                       .
    /datasets/set2        **/*.nii  (recursive)       madeup

this should yield File/Image objects like

    filename        | source_path           | sub_path
    file1.nii       | /datasets/set1        | .
    file2.nii       | /datasets/set1        | .
    file1.nii       | /datasets/set2        | madeup
    file2.nii       | /datasets/set2        | madeup
    subfile1.nii    | /datasets/set2/sub    | madeup/sub

`source_path` where the object actually came from
`sub_path` contains a custom part and the sub-paths below original `source_directory`


# useful links

- [Orientation and Voxel-Order Terminology: RAS, LAS, LPI, RPI, XYZ and All That](http://www.grahamwideman.com/gw/brain/orientation/orientterms.htm)
- [NIfTI-1 Test Data](https://nifti.nimh.nih.gov/nifti-1/data/)
- [Atlases from the NIST lab at the BIC](https://nist.mni.mcgill.ca/atlases/)