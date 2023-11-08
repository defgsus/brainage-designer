import {createSliceSaga} from "redux-toolkit-saga";
import {call, put, select} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {API_URLS} from "/src/app/urls";
import {setFileList, setImageVolume, setImageMeta} from "./form-slice";

export const normalize_path = (path) => {
    if (typeof path !== "string")
        return path;
    while (path.startsWith("/"))
        path = path.slice(1);
    return `/${path}`;
}

export const formSaga = createSliceSaga({
    name: "formSaga",
    caseSagas: {
        *requestFileList(action) {
            let {path, recursive, namespace} = action.payload;
            path = normalize_path(path);

            const api = yield* get_api();
            try {
                const response = yield call(() => api.get(
                    API_URLS.FILES.BROWSE,
                    {params: {path, recursive: recursive ? 1 : undefined}}
                ));
                yield put(setFileList({namespace, data: response.data}));
            }
            catch (e) {
                console.log(`Listing error for ${path}`);
            }
        },
        *requestImageMeta(action) {
            let {path} = action.payload;
            path = normalize_path(path);

            const api = yield* get_api();
            try {
                const response = yield call(() => api.get(
                    API_URLS.FILES.IMAGE.META,
                    {params: {path}}
                ));
                yield put(setImageMeta(response.data));
            }
            catch (e) {
                if (e?.response?.status === 404) {
                    yield put(setImageMeta({path, error: "Not found"}));
                } else {
                    yield put(setImageMeta({path, error: "Error reading image"}));
                }
            }
        },
        *requestImageVolume(action) {
            let {path} = action.payload;
            path = normalize_path(path);

            const api = yield* get_api({
                responseType: "arraybuffer",
            });
            try {
                const response = yield call(() => api.get(
                    API_URLS.FILES.IMAGE.BLOB,
                    {params: {path}}
                ));

                let [shape, zooms, range, dtype] = response.headers["x-image-meta"].split(";");
                shape = shape.split(",").map(s => parseInt(s));
                zooms = zooms.split(",").map(s => parseFloat(s));
                range = range.split(",").map(s => parseFloat(s));

                yield put(setImageVolume({
                    path,
                    shape,
                    range,
                    zooms,
                    dtype,
                    data: new Float32Array(response.data),
                }));
            }
            catch (e) {
                if (e?.response?.status === 404) {
                    yield put(setImageVolume({path, error: "Not found"}));
                } else {
                    yield put(setImageVolume({path, error: "Error reading image"}));
                }
            }
        },
    },
});

export const {
    requestFileList,
    requestImageMeta,
    requestImageVolume,
} = formSaga.actions;
