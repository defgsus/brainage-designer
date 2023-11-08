import {createSliceSaga} from "redux-toolkit-saga";
import {call, put} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {
    setAnalysisAverageResultResponse,
    setAnalysisCreateResponse,
    setAnalysisResponse,
    setAnalysisResultResponse,
    setAnalysisSourcePreviewResponse
} from "./analysis-slice";
import {requestTableSaga} from "/src/features/tableview/tableview-saga";
import {API_URLS, APP_URLS} from "/src/app/urls";
import {successNotification} from "/src/common/notifications";
import {history} from "../../store";


export const analysisSaga = createSliceSaga({
    name: "analysisSaga",
    caseSagas: {
        *requestAnalysis(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            yield put(setAnalysisSourcePreviewResponse(null));
            const response = yield call(() =>
                api.get(API_URLS.ANALYSIS.GET.replace(":uuid", uuid))
            );
            yield put(setAnalysisResponse(response.data));
        },
        *requestAnalysisCreate(action) {
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.ANALYSIS.CREATE, action.payload)
            );
            yield put(setAnalysisCreateResponse(response.data));
            yield* requestTableSaga({payload: {url: API_URLS.ANALYSIS.TABLE}});
        },
        *requestAnalysisUpdate(action) {
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.ANALYSIS.POST.replace(":uuid", action.payload.uuid), action.payload)
            );
            yield put(setAnalysisResponse(response.data));
            successNotification({message: "pipeline stored"});
        },
        *requestAnalysisRun(action) {
            const {uuid, data} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.ANALYSIS.START_PROCESS.replace(":uuid", uuid), data)
            );
            successNotification({message: "pipeline queued"});
        },
        *requestAnalysisStop(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.ANALYSIS.STOP_PROCESS.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline stopped"});
        },
        *requestAnalysisCopy(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.post(API_URLS.ANALYSIS.COPY.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline copied"});
            const new_uuid = response.data.uuid;
            yield call(() => history.push(APP_URLS.ANALYSIS.VIEW.replace(":ap_id", new_uuid)));
        },
        *requestAnalysisDelete(action) {
            const {uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.delete(API_URLS.ANALYSIS.POST.replace(":uuid", uuid))
            );
            successNotification({message: "pipeline deleted"});
            yield call(() => history.push(APP_URLS.DASHBOARD));
        },
        *requestAnalysisSourcePreview(action) {
            const {uuid, parameter_values} = action.payload;
            const api = yield* get_api();
            try {
                const response = yield call(() =>
                    api.post(API_URLS.ANALYSIS.SOURCE_PREVIEW.replace(":uuid", uuid), {
                        parameter_values
                    })
                );
                yield put(setAnalysisSourcePreviewResponse(response.data));
            }
            catch (e) {
                let error = "something went wrong fetching the files";
                if (e.response?.data?.error)
                    error = e.response.data.error;
                yield put(setAnalysisSourcePreviewResponse({error}));
            }
        },
        *requestAnalysisResult(action) {
            const {uuid: result_uuid} = action.payload;
            const api = yield* get_api();
            const response = yield call(() =>
                api.get(API_URLS.ANALYSIS.RESULTS.GET.replace(":uuid", result_uuid))
            );
            yield put(setAnalysisResultResponse(response.data));
        },
        *requestAnalysisAverageResult(action) {
            const {uuid: analysis_uuid} = action.payload;
            const api = yield* get_api();
            try {
                const response = yield call(() =>
                    api.get(API_URLS.ANALYSIS.RESULT.replace(":uuid", analysis_uuid))
                );
                yield put(setAnalysisAverageResultResponse(response.data));
            } catch (error) {
                yield put(setAnalysisAverageResultResponse(null));
            }
        },
    },
});

export const {
    requestAnalysis,
    requestAnalysisCreate,
    requestAnalysisUpdate,
    requestAnalysisRun,
    requestAnalysisStop,
    requestAnalysisCopy,
    requestAnalysisDelete,
    requestAnalysisSourcePreview,
    requestAnalysisResult,
    requestAnalysisAverageResult,
} = analysisSaga.actions;
