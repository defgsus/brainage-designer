import React, {useEffect, useState} from "react";
import { Route, Routes, useLocation } from 'react-router';
import { ReduxRouter, push } from '@lagunovsky/redux-react-router'
import {DndProvider} from "react-dnd";
import {HTML5Backend} from "react-dnd-html5-backend";
import ErrorBoundary from "./ErrorBoundary";
import { history, store } from "/src/store";
import Dashboard from "/src/features/dashboard/Dashboard";
import MainLayout from "/src/common/MainLayout";
import {useAppDispatch, useAppSelector} from "./hooks";
import WebSocketProvider from "/src/features/ws/WebSocketProvider";
import {APP_URLS} from "./urls";
import PreprocessingView from "/src/features/preprocessing/PreprocessingView";
import ProcessView from "/src/features/process/ProcessView";
import TestBrowser from "/src/features/test/TestBrowser";
import TestFlex from "/src/features/test/TestFlex";
import ImagePage from "/src/features/files/ImagePage";
import TestVolumeShader from "/src/features/test/TestVolumeShader";
import ImageVolumePage from "/src/features/files/ImageVolumePage";
import AnalysisView from "../features/analysis/AnalysisView";


const App = () => {
    const dispatch = useAppDispatch();

    const routes = [
        {path: APP_URLS.DASHBOARD, content: <Dashboard/>},
        {path: APP_URLS.PROCESS.VIEW, content: <ProcessView/>},
        {path: APP_URLS.PREPROCESSING.VIEW, content: <PreprocessingView/>},
        {path: APP_URLS.ANALYSIS.VIEW, content: <AnalysisView/>},
        {path: APP_URLS.FILES.IMAGE, content: <ImagePage/>},
        {path: APP_URLS.FILES.VOLUME, content: <ImageVolumePage/>},

        {path: APP_URLS.TEST.BROWSER, content: <TestBrowser/>},
        {path: APP_URLS.TEST.FLEX, content: <TestFlex/>},
        {path: APP_URLS.TEST.SHADER, content: <TestVolumeShader/>},
    ]

    return (
        <ReduxRouter history={history} store={store}>
            <WebSocketProvider>
                <MainLayout>
                    <DndProvider backend={HTML5Backend}>
                        <Routes>
                            {routes.map(route => (
                                <Route
                                    key={route.path}
                                    path={route.path}
                                    element={
                                        <ErrorBoundary>
                                            {route.content}
                                        </ErrorBoundary>
                                    }
                                />
                            ))}

                            <Route element={
                                <div>404</div>
                            }/>
                        </Routes>
                    </DndProvider>
                </MainLayout>
            </WebSocketProvider>
        </ReduxRouter>
    );
};

export default App;

