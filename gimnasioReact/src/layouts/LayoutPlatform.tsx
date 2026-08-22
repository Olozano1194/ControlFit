import { Outlet, useLocation } from "react-router-dom";
import { useEffect, useRef } from "react";

import SideBarPlatform from "../components/SideBarPlatform";
import Header from "../components/Header";
import { useAuth } from "../context/useAuth";
import { useInactivityTimeout } from "../hooks/useInactivityTimeout";
import { startSilentRefresh, stopSilentRefresh } from "../api/axios/axios.private";

const INACTIVITY_MINUTES = 30;

function LayoutPlatform() {
    const { logout } = useAuth();
    const location = useLocation();
    const { resetTimer } = useInactivityTimeout(INACTIVITY_MINUTES, logout);

    useEffect(() => {
        startSilentRefresh();
        return () => stopSilentRefresh();
    }, []);

    const prevPath = useRef(location.pathname);
    useEffect(() => {
        if (prevPath.current !== location.pathname) {
            resetTimer();
            prevPath.current = location.pathname;
        }
    }, [location.pathname, resetTimer]);

    return (
        <div className="min-h-screen grid grid-cols-1 xl:grid-cols-6">
            <SideBarPlatform />

            <div className="xl:col-span-5">
                <Header />
                <div className="h-[90vh] overflow-y-scroll p-8">
                    <Outlet />
                </div>
            </div>
        </div>
    );
}
export default LayoutPlatform;