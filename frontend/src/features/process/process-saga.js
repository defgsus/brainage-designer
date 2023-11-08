import {createSliceSaga} from "redux-toolkit-saga";
import {call, put} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {API_URLS} from "/src/app/urls";
import {setProcessModuleObjects, setProcessResponse} from "./process-slice";


export const processSaga = createSliceSaga({
    name: "processSaga",
    caseSagas: {
        *requestProcess(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.get(API_URLS.PROCESS.GET.replace(":uuid", uuid))
            );
            yield put(setProcessResponse(response.data));
        },
        *requestModuleObjects(action) {
            // source = "source" or "target"
            const {process_uuid, module_uuid, source} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.get(API_URLS.PROCESS.OBJECT.BY_MODULE, {
                    params: {
                        process_uuid,
                        module_uuid,
                        source,
                    },
                })
            );
            yield put(setProcessModuleObjects({process_uuid, module_uuid, response: response.data}));
        },
    },
});

export const {
    requestProcess,
    requestModuleObjects,
} = processSaga.actions;
