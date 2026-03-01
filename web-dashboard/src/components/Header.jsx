import { useState, useEffect, useRef } from 'react';

const LAYOUT_OPTIONS = [
    { label: "🔲 Default Layout", value: "[0,1,2,3]" },
    { label: "↔️ Swap East ↔ West", value: "[0,1,3,2]" },
    { label: "↕️ Swap North ↔ South", value: "[1,0,2,3]" },
    { label: "🔄 Swap N↔E and S↔W", value: "[2,3,0,1]" },
    { label: "🔁 Reverse Order", value: "[3,2,1,0]" }
];

export default function Header({ metrics, uptime, isConnected, currentView, setCurrentView }) {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [selectedLayout, setSelectedLayout] = useState(LAYOUT_OPTIONS[0]);
    const dropdownRef = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsDropdownOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const fps = parseFloat(metrics?.fps || metrics?.current_fps || 0).toFixed(1);
    const veh = metrics?.total_vehicles || metrics?.vehicle_count || 0;

    // ─── Environment Impact Calculations ───
    const vehRef = useRef(0);
    useEffect(() => {
        vehRef.current = veh;
    }, [veh]);

    const [idleSavedSec, setIdleSavedSec] = useState(0);
    useEffect(() => {
        const interval = setInterval(() => {
            // Estimate: AI saves 0.5 seconds of idle time per second for each tracked vehicle
            setIdleSavedSec(prev => prev + (vehRef.current * 0.5));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    // 1️⃣ Idle Time Reduced → seconds converted into hours
    const idleHours = idleSavedSec / 3600;
    // 2️⃣ Fuel Rate → approx 0.8 liters/hour
    const fuelSaved = idleHours * 0.8;
    // 3️⃣ Total CO₂ Reduced = Fuel Saved × 2.31 kg
    const co2Reduced = fuelSaved * 2.31;
    // ───────────────────────────────────────

    const [isLiveMode, setIsLiveMode] = useState(false);

    // ... (rest of the component) ...
    // Note: I am placing the state inline as a temporary toggle.

    return (
        <header>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '24px' }}>🚦</span>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: '700', fontSize: '15px', letterSpacing: '0.5px' }}>
                        AI Traffic Control System
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                        YOLOv8 Detection &bull; Adaptive Signal Control
                    </span>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '12px', alignItems: 'center' }}>
                <button
                    onClick={() => setCurrentView('dashboard')}
                    style={{
                        background: currentView === 'dashboard' ? 'var(--blue)' : 'transparent',
                        color: currentView === 'dashboard' ? '#fff' : 'var(--muted)',
                        border: 'none', padding: '8px 16px', borderRadius: '8px',
                        fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}>
                    🚦 Live Dashboard
                </button>
                <button
                    onClick={() => setCurrentView('incidents')}
                    style={{
                        background: currentView === 'incidents' ? 'var(--red)' : 'transparent',
                        color: currentView === 'incidents' ? '#fff' : 'var(--muted)',
                        border: 'none', padding: '8px 16px', borderRadius: '8px',
                        fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}>
                    ⚠️ Incident Feed
                </button>
                <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }}></div>

                <div ref={dropdownRef} style={{ position: 'relative' }}>
                    <button
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        disabled={isLiveMode}
                        style={{
                            background: isDropdownOpen ? '#020617' : '#020617',
                            color: isLiveMode ? 'var(--muted)' : '#fff',
                            border: '1px solid',
                            borderColor: isDropdownOpen ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)',
                            padding: '8px 16px',
                            borderRadius: '8px',
                            fontSize: '13px',
                            fontWeight: '600',
                            cursor: isLiveMode ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                            boxShadow: isDropdownOpen ? '0 4px 12px rgba(0,0,0,0.5)' : 'none',
                        }}
                    >
                        <span>{selectedLayout.label}</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                            style={{ transition: 'transform 0.2s', transform: isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>

                    {isDropdownOpen && !isLiveMode && (
                        <div style={{
                            position: 'absolute',
                            top: 'calc(100% + 8px)',
                            right: 0,
                            background: '#020617',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '12px',
                            padding: '6px',
                            width: '200px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '4px',
                            boxShadow: '0 10px 25px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05) inset',
                            zIndex: 100,
                            animation: 'dropdownFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
                        }}>
                            {LAYOUT_OPTIONS.map((option, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => {
                                        setSelectedLayout(option);
                                        setIsDropdownOpen(false);
                                        const mapping = JSON.parse(option.value);
                                        fetch(`http://${window.location.hostname}:8000/api/swap-video`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ mapping })
                                        }).catch(err => console.error("Swap error:", err));
                                    }}
                                    style={{
                                        background: selectedLayout.value === option.value ? 'rgba(255,255,255,0.1)' : 'transparent',
                                        color: selectedLayout.value === option.value ? '#fff' : 'var(--muted)',
                                        border: 'none',
                                        padding: '8px 12px',
                                        borderRadius: '6px',
                                        fontSize: '13px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        textAlign: 'left',
                                        transition: 'all 0.1s',
                                        display: 'flex',
                                        alignItems: 'center'
                                    }}
                                    onMouseEnter={e => {
                                        if (selectedLayout.value !== option.value) {
                                            e.target.style.background = 'rgba(255,255,255,0.05)';
                                            e.target.style.color = '#fff';
                                        }
                                    }}
                                    onMouseLeave={e => {
                                        if (selectedLayout.value !== option.value) {
                                            e.target.style.background = 'transparent';
                                            e.target.style.color = 'var(--muted)';
                                        }
                                    }}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }}></div>

                {!isLiveMode ? (
                    <button
                        onClick={() => {
                            fetch(`http://${window.location.hostname}:8000/api/open-live-camera`, { method: 'POST' })
                                .then(() => setIsLiveMode(true))
                                .catch(err => console.error('Failed to open live camera', err));
                        }}
                        style={{
                            background: 'rgba(56, 189, 248, 0.15)',
                            color: '#38bdf8',
                            border: '1px solid rgba(56, 189, 248, 0.4)',
                            padding: '8px 16px', borderRadius: '8px',
                            fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                            transition: 'all 0.2s',
                            display: 'flex', alignItems: 'center', gap: '6px'
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.25)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
                    >
                        🎥 Start Live Feed
                    </button>
                ) : (
                    <button
                        onClick={() => {
                            fetch(`http://${window.location.hostname}:8000/api/close-live-camera`, { method: 'POST' })
                                .then(() => setIsLiveMode(false))
                                .catch(err => console.error('Failed to close live camera', err));
                        }}
                        style={{
                            background: 'rgba(239, 68, 68, 0.15)',
                            color: '#ef4444',
                            border: '1px solid rgba(239, 68, 68, 0.4)',
                            padding: '8px 16px', borderRadius: '8px',
                            fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                            transition: 'all 0.2s',
                            display: 'flex', alignItems: 'center', gap: '6px'
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.25)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)'}
                    >
                        ⏹ Stop Live Feed
                    </button>
                )}
            </div>

            <style>{`
                @keyframes dropdownFadeIn {
                    from { opacity: 0; transform: translateY(-8px) scale(0.95); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
            `}</style>

            <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: '#f59e0b', fontSize: '18px', fontWeight: '700' }}>
                        {fuelSaved.toFixed(4)}<span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: '2px' }}>L</span>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase' }}>Fuel Saved</div>
                </div>

                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: '#10b981', fontSize: '18px', fontWeight: '700' }}>
                        {co2Reduced.toFixed(4)}<span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: '2px' }}>kg</span>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase' }}>CO₂ Reduced</div>
                </div>

                <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }}></div>

                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: 'var(--green)', fontSize: '18px', fontWeight: '700' }}>
                        {fps}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase' }}>FPS</div>
                </div>

                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: 'var(--blue)', fontSize: '18px', fontWeight: '700' }}>
                        {veh}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase' }}>Vehicles</div>
                </div>

                <div style={{ textAlign: 'center' }}>
                    <div className="mono" style={{ color: 'var(--purple)', fontSize: '18px', fontWeight: '700' }}>
                        {uptime}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase' }}>Uptime</div>
                </div>

                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        border: isConnected ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
                        padding: '6px 12px',
                        borderRadius: '20px',
                        fontSize: '11px',
                        fontWeight: '600'
                    }}
                >
                    {isConnected && <div className="live-pulse" />}
                    {isConnected ? 'LIVE' : 'DISCONNECTED'}
                </div>
            </div>
        </header>
    );
}
