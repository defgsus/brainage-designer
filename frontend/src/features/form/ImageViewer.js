import {Checkbox, Image, InputNumber, Select, Switch} from "antd";
import {useEffect, useState} from "react";
import {API_URLS} from "/src/app/urls";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {requestImageMeta} from "./form-saga";
import Json from "/src/common/Json";
import Flex from "/src/common/Flex";
import "./ImageViewer.scss"
import Error from "../../common/Error";


const ImageViewer = ({filename, ...props}) => {
    const dispatch = useAppDispatch();
    const {image_meta} = useAppSelector(state => state.form);
    const [image_src, set_image_src] = useState(null);
    const [image_src_2, set_image_src_2] = useState(null);
    const [error, set_error] = useState(null);
    const [meta_loading, set_meta_loading] = useState(false);
    const [plot_type, set_plot_type] = useState("epi");
    const [slice_offsets, set_slice_offsets] = useState([0, 0, 0]);
    const [slice_offset_enabled, set_slice_offset_enabled] = useState(false);

    const meta = image_meta[filename];

    useEffect(() => {
        set_slice_offsets([0, 0, 0]);
        set_slice_offset_enabled(false);
    }, [filename]);

    useEffect(() => {
        if (!filename) {
            set_image_src(null);
            return;
        }

        let query = {
            path: filename,
            plot: plot_type,
        };
        set_image_src_2(`${API_URLS.FILES.IMAGE.PLOT}?${new URLSearchParams(query)}`)

        query = {
            path: filename,
        };
        if (slice_offset_enabled) {
            for (const i in slice_offsets)
                query[`o${i}`] = slice_offsets[i];
        }
        set_image_src(`${API_URLS.FILES.IMAGE.SLICES}?${new URLSearchParams(query)}`);

        if (!meta) {
            if (!meta_loading) {
                set_meta_loading(true);
                dispatch(requestImageMeta({path: filename}));
            }
        } else {
            set_meta_loading(false);
            if (meta.error) {
                set_error(meta.error);
            } else {
                set_error(null);

                let new_slice_offsets = [...slice_offsets].slice(0, meta.shape.length);
                while (new_slice_offsets.length < meta.shape.length)
                    new_slice_offsets.push(0);

                for (const i in slice_offsets) {
                    if (new_slice_offsets[i] >= meta.shape.length[i])
                        new_slice_offsets[i] = meta.shape.length[i] - 1;
                }

                if (new_slice_offsets.length !== slice_offsets.length
                    || JSON.stringify(new_slice_offsets) !== JSON.stringify(slice_offsets)
                ) {
                    set_slice_offsets(new_slice_offsets);
                }

            }
        }

    }, [filename, meta, plot_type, slice_offsets, slice_offset_enabled]);

    const handle_offset_change = (value, axis) => {
        if (meta?.shape?.length && axis < meta.shape.length) {
            value = Math.max(0, Math.min(meta.shape[axis] - 1, value));
            const new_offsets = [...slice_offsets];
            new_offsets[axis] = value;
            set_slice_offsets(new_offsets);
        }
    }
    const meta_values = [
        {name: "resolution", value: !meta?.shape ? "?" : meta.shape.join(" x ")},
        {name: "voxel size", value: !meta?.voxel_size ? "?" : meta.voxel_size.join(" x ")},
        {name: "dtype", value: !meta?.dtype ? "?" : meta.dtype},
    ];
    return (
        <div className={"image-viewer"}>
            <Flex.Row marginX={".3rem"}>
                <Flex.Item>
                    <Flex.Col marginY={".3rem"}>
                        {meta_values.map(elem => (
                            <Flex.Item key={elem.name}>
                                <div><b>{elem.name}</b>:</div>
                                <div>{elem.value}</div>
                            </Flex.Item>
                        ))}
                    </Flex.Col>
                </Flex.Item>

                <Flex.Item>
                    {!error ? null : <Error>{error}</Error>}

                    <Flex.Col margin={"1rem"}>
                        <Flex.Item>
                            <div><b>{"slice offset"}</b>:</div>
                            <Flex.Row marginX={".1rem"} align={"center"}>
                                <div>
                                    <Switch
                                        checked={slice_offset_enabled}
                                        onChange={set_slice_offset_enabled}
                                    />
                                </div>
                                <Flex.Row margin={".3rem"}>
                                    {slice_offsets.map((o, i) => (
                                        <InputNumber
                                            value={o}
                                            onChange={(v) => handle_offset_change(v, i)}
                                            disabled={!slice_offset_enabled}
                                        />
                                    ))}
                                </Flex.Row>
                            </Flex.Row>
                            <Image src={image_src} {...props}/>
                        </Flex.Item>

                        <div>
                            <Flex.Row>
                                <div>
                                    <div><b>plot type</b>:</div>
                                    <Select
                                        value={plot_type}
                                        onChange={v => set_plot_type(v)}
                                    >
                                        <Select.Option value={"anat"}>grayscale</Select.Option>
                                        <Select.Option value={"epi"}>colored</Select.Option>
                                        <Select.Option value={"glass_brain"}>glass brain</Select.Option>
                                    </Select>
                                </div>
                            </Flex.Row>
                            <Image src={image_src_2} {...props}/>
                        </div>
                    </Flex.Col>

                </Flex.Item>
            </Flex.Row>
            {/*<Json data={image_meta[filename] || null}/>*/}
        </div>
    )
};

export default ImageViewer;

