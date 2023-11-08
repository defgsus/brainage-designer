import {useEffect, useRef, useState} from "react";
import VolumeRenderer from "/src/features/graphics/VolumeRenderer";
import {normalize_path, requestImageVolume} from "/src/features/form/form-saga";
import {clearImageVolume} from "/src/features/form/form-slice";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";


const ImageVolumeViewer = ({path, width, height, ...props}) => {

    const dispatch = useAppDispatch();
    const {image_volumes} = useAppSelector(state => state.form);
    const [local_path, set_local_path] = useState(null);
    const [requested_path, set_requested_path] = useState(null);

    useEffect(() => {
        // clear volume on close
        return () => {
            if (local_path)
                dispatch(clearImageVolume({path: local_path}));
        }
    }, []);

    useEffect(() => {
        const new_path = normalize_path(path);
        if (new_path !== local_path) {
            if (local_path && local_path !== requested_path)
                dispatch(clearImageVolume({path: local_path}));
            set_local_path(new_path);
        }
    }, [path, local_path, requested_path]);


    useEffect(() => {
        if (local_path) {
            if (!image_volumes[local_path]) {
                set_requested_path(local_path);
                dispatch(requestImageVolume({path: local_path}));
            }
        }

    }, [local_path, image_volumes]);

    //console.log("XX", local_path, Object.keys(image_volumes));

    return (
        <div>
            <VolumeRenderer
                width={width}
                height={height}
                image={image_volumes[local_path]}
            />
        </div>
    );
};

export default ImageVolumeViewer;

