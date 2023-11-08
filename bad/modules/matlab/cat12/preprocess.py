from bad.modules.base import ModuleTag
from .base import *


class Cat12Preprocess(Cat12ModuleBase):
    name = "cat12_preprocess"
    tags = [ModuleTag.MULTI_IMAGE_PROCESS]
    handles_nii_gz = True

    parameters = [
        ParameterFloat(
            name="normalized_voxel_size", default_value=1.5,
        ),
        ParameterFloat(
            name="local_adaption_strength", default_value=.5,
            min_value=0., max_value=1.,
        ),
        ParameterFloat(
            name="bias_correction_strength", default_value=.5,
            min_value=0., max_value=1.,
        ),
        ParameterSelect(
            name="noise_correction", default_value="auto",
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option("auto", "auto"),
                ParameterSelect.Option(1, "full"),
                ParameterSelect.Option(2, "ISARNLM"),
            ]
        ),
        ParameterSelect(
            name="skull_stripping_strength", default_value=2,
            options=[
                ParameterSelect.Option(-1, "none"),
                ParameterSelect.Option(1, "SPM approach"),
                ParameterSelect.Option(2, "new APRG approach"),
            ]
        ),
        ParameterFloat(
            name="cleanup_strength", default_value=.5,
            min_value=0., max_value=1.,
        ),
        ParameterSelect(
            name="output_surface", default_value=0,
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1, "lh+rh"),
                ParameterSelect.Option(2, "lh+rh+cerebellum"),
                ParameterSelect.Option(3, "lh"),
                ParameterSelect.Option(4, "rh"),
                ParameterSelect.Option(5, "lh+rh (fast)"),
                ParameterSelect.Option(6, "lh+rh+cerebellum (fast)"),
                ParameterSelect.Option(9, "thickness only"),
                # TODO: +10 to estimate WM and CSF width/depth/thickness (experimental!)
            ]
        ),
        ParameterBool(
            name="output_bids", default_value=True,
        ),
        ParameterBool(
            name="gray_matter_native", default_value=False,
        ),
        ParameterBool(
            name="gray_matter_warped", default_value=False,
        ),
        ParameterSelect(
            name="gray_matter_mod", default_value=1,
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1, "affine+nonlinear"),
                ParameterSelect.Option(2, "nonlinear only"),
                ParameterSelect.Option(3, "both"),
            ]
        ),
        ParameterSelect(
            name="gray_matter_dartel", default_value=0,
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1, "rigid"),
                ParameterSelect.Option(2, "affine"),
                ParameterSelect.Option(3, "both"),
            ]
        ),
        ParameterSelect(
            name="affine_preprocessing", default_value=1070,
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1070, "default"),
                ParameterSelect.Option(1144, "default (update)"),
                ParameterSelect.Option(1, "light"),
                ParameterSelect.Option(2, "full"),
                ParameterSelect.Option(5, "animal"),
            ]
        ),
        ParameterBool(
            name="center_of_mass_origin", default_value=True,
            description="Use center-of-mass approach for estimating origin",
        ),
        ParameterBool(
            name="modify_affine_scaling", default_value=False,
        ),
        ParameterSelect(
            name="stroke_lesion_detection", default_value=0,
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1, "manual"),
                ParameterSelect.Option(2, "automatic (development)"),
            ]
        ),
        ParameterSelect(
            name="affine_regularisation", default_value="mni",
            options=[
                ParameterSelect.Option("none", "none"),
                ParameterSelect.Option("mni", "mni"),
                ParameterSelect.Option("eastern", "eastern"),
                ParameterSelect.Option("subj", "subject"),
                ParameterSelect.Option("rigid", "rigid"),
            ]
        ),
        ParameterSelect(
            name="output_pdf", default_value=2,
            description="display and print out pdf-file of results",
            options=[
                ParameterSelect.Option(0, "none"),
                ParameterSelect.Option(1, "volume"),
                ParameterSelect.Option(2, "volume & surface"),
            ],
        ),
        *Cat12ModuleBase.parameters,
    ]

    def process_nii_files(
            self,
            input_images: Iterable[ImageObject],
            image_filenames: Iterable[Path],
            stub: bool = False,
    ) -> Generator[Union[ImageObject, FileObject], None, None]:
        if not stub:
            parameter_map = {
                "spm.tools.cat.estwrite.output.surface": "output_surface",
                "spm.tools.cat.estwrite.output.BIDS.BIDSno": "output_bids",
                "spm.tools.cat.estwrite.extopts.registration.vox": "normalized_voxel_size",
                "spm.tools.cat.estwrite.extopts.segmentation.LASstr": "local_adaption_strength",
                "spm.tools.cat.estwrite.extopts.segmentation.APP": "affine_preprocessing",
                "spm.tools.cat.estwrite.opts.biasstr": "bias_correction_strength",
                "spm.tools.cat.estwrite.opts.affreg": "affine_regularisation",
                "spm.tools.cat.estwrite.extopts.segmentation.NCstr": "noise_correction",
                "spm.tools.cat.estwrite.extopts.segmentation.gcutstr": "skull_stripping_strength",
                "spm.tools.cat.estwrite.extopts.segmentation.cleanupstr": "cleanup_strength",
                "spm.tools.cat.estwrite.extopts.segmentation.setCOM": "center_of_mass_origin",
                "spm.tools.cat.estwrite.extopts.segmentation.affmod": "modify_affine_scaling",
                "spm.tools.cat.estwrite.extopts.segmentation.SLC": "stroke_lesion_detection",
                "spm.tools.cat.estwrite.output.GM.native": "gray_matter_native",
                "spm.tools.cat.estwrite.output.GM.warped": "gray_matter_warped",
                "spm.tools.cat.estwrite.output.GM.mod": "gray_matter_mod",
                "spm.tools.cat.estwrite.output.GM.dartel": "gray_matter_dartel",
                "spm.tools.cat.estwrite.extopts.admin.print": "output_pdf",
            }

            parameters = {
                "spm.tools.cat.estwrite.extopts.admin.ignoreErrors": 0,  # stop on errors
            }

            for setting_name, param_name in parameter_map.items():
                value = self.get_parameter_value(param_name)
                if param_name == "noise_correction" and value == "auto":
                    value = float("-Inf")
                parameters[setting_name] = value

            self.call_cat12(
                "cat_standalone_segment",
                *image_filenames,
                parameters=parameters,
            )

        # TODO: Lots actually!
        #   One thing: we could actually check for finished files parallel to the cat12 call
        #   and pass them on already.

        image_prefixes = [
            "mwp1", "mwp2", "p0", "wm", "y_",
        ]

        for image, fn in zip(input_images, image_filenames):
            for prefix in image_prefixes:
                output_filename = fn.parent / "mri" / f"{prefix}{strip_compression_extension(fn.name)}"
                if output_filename.exists() or stub:
                    yield self.image_replace(
                        image,
                        action_name=f"cat12:{prefix}",
                        src=output_filename if not stub else None,
                        filename_prefix=f"{prefix.rstrip('_')}_",
                        sub_path=image.sub_path / "mri",
                    )
