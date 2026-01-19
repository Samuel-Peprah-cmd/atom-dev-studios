window.addEventListener('load', () => {
    const bar = document.getElementById('progress');
    const loader = document.getElementById('loader');
    
    // Smooth progress simulation
    setTimeout(() => bar.style.width = '40%', 100);
    setTimeout(() => bar.style.width = '100%', 500);
    
    setTimeout(() => {
        loader.style.opacity = '0';
        setTimeout(() => loader.style.display = 'none', 500);
    }, 1200);
});

// Auto-hide flash messages after 5 seconds
setTimeout(() => {
    const flash = document.getElementById('flash-container');
    if (flash) {
        flash.style.transition = 'opacity 1s ease';
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 1000);
    }
}, 5000);