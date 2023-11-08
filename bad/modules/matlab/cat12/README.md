use R2017b v93 https://www.mathworks.com/products/compiler/matlab-runtime.html

- **WM**: **W**hite **M**atter
- **GM**: **G**ray **M**atter
- **NC**: **N**oise **C**orrection
  - **SANLM**: 
  - **ISARNLM**:
- **APP**: **A**ffine **P**re**p**rocessing (with bias correction)
- **LAS**: **L**ocal **A**daptive **S**egmentation
- **BVC**: **B**lood **V**essel **C**orrection
- **REG**: Optimized Shooting **Reg**istration
- **CSF**: 
- **BIDS**:
- **RMS**: 

```shell

# well, this does not work
./standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ./standalone/cat_standalone_segment.m \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.print = 1;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.surface = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.BIDS.BIDSno = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.GM.mod = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.WM.mod = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.label.native = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.bias.warped = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.warps = [0 0];" \
  ~/prog/data/datasets/ixi/IXI002-Guys-0828-T1.nii.gz

./standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ./standalone/cat_standalone_segment_TEST.m \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.print = 1;" \
  ~/prog/data/datasets/ixi/IXI002-Guys-0828-T1.nii.gz

./standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ./standalone/cat_standalone_segment.m \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.print = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.ignoreErrors = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.surface = 2;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.BIDS.BIDSno = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.vox = 1.5;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.LASstr = 0.5;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.APP = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.opts.biasstr = 0.5;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.opts.affreg = 'none';" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.gcutstr = 2;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.cleanupstr = 0.5;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.setCOM = 1;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.affmod = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.SLC = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.GM.native = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.GM.warped = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.GM.mod = 0;" \
  -a "matlabbatch{1}.spm.tools.cat.estwrite.output.GM.dartel = 0;" \
  ~/prog/data/datasets/ixi/IXI002-Guys-0828-T1.nii.gz

# all below do not support nii.gz files!!

# defacing 
./standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ./standalone/cat_standalone_deface.m \
  ~/prog/data/datasets/ixi/IXI*.nii

# smooth (no images found error)
./standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ./standalone/cat_standalone_smooth.m \
  -a1 "[12,12,12]" -a2 " 's12' " \
  ~/prog/data/datasets/ixi/IXI*.nii 
  

# not working yet
~/Downloads/prog/matlab/cat12_latest_R2017b_MCR_Linux/CAT12.8.1_r2042_R2017b_MCR_Linux/standalone/cat_standalone.sh \
  -m ~/prog/MATLAB_Runtime/v93 \
  -b ~/Downloads/prog/matlab/cat12_latest_R2017b_MCR_Linux/CAT12.8.1_r2042_R2017b_MCR_Linux/standalone/cat_standalone_simple.m \
  ~/prog/data/datasets/ixi/*.nii.gz

```
