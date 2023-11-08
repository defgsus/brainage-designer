import {createSliceSaga} from "redux-toolkit-saga";
import {call, put} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {setPreprocessCreateResponse, setPreprocessResponse} from "./preprocessing-slice";
import {requestTableSaga} from "/src/features/tableview/tableview-saga";
import {API_URLS, APP_URLS} from "/src/app/urls";
import {successNotification} from "/src/common/notifications";
import {history} from "../../store";


export const preprocessingSaga = createSliceSaga({
    name: "preprocessingSaga",
    caseSagas: {
        *requestPreprocess(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.get(API_URLS.PREPROCESSING.GET.replace(":uuid", uuid))
            );
            yield put(setPreprocessResponse(response.data));
        },
        *requestPreprocessCreate(action) {
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.PREPROCESSING.CREATE, action.payload)
            );
            yield put(setPreprocessCreateResponse(response.data));
            yield* requestTableSaga({payload: {url: API_URLS.PREPROCESSING.TABLE}});
        },
        *requestPreprocessUpdate(action) {
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.PREPROCESSING.POST.replace(":uuid", action.payload.uuid), action.payload)
            );
            yield put(setPreprocessResponse(response.data));
            successNotification({message: "pipeline stored"});
        },
        *requestPreprocessRun(action) {
            const {uuid, data} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.PREPROCESSING.START_PROCESS.replace(":uuid", uuid), data)
            );
            successNotification({message: "pipeline queued"});
        },
        *requestPreprocessStop(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.PREPROCESSING.STOP_PROCESS.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline stopped"});
        },
        *requestPreprocessCopy(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.PREPROCESSING.COPY.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline copied"});
            const new_uuid = response.data.uuid;
            yield call(() => history.push(APP_URLS.PREPROCESSING.VIEW.replace(":pp_id", new_uuid)));
        },
        *requestPreprocessDelete(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.delete(API_URLS.PREPROCESSING.POST.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline deleted"});
            yield call(() => history.push(APP_URLS.DASHBOARD));
        },
    },
});

export const {
    requestPreprocess,
    requestPreprocessCreate,
    requestPreprocessUpdate,
    requestPreprocessRun,
    requestPreprocessStop,
    requestPreprocessCopy,
    requestPreprocessDelete,
} = preprocessingSaga.actions;
