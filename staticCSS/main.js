// Основные JavaScript функции для Эко-Города

// Инициализация карты выбора
function initMapPicker() {
    if (document.getElementById('mapPicker')) {
        const map = L.map('mapPicker').setView([51.527623, 81.217673], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
        
        // Добавляем маркер при клике
        let marker;
        map.on('click', function(e) {
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker(e.latlng).addTo(map);
            document.getElementById('latitude').value = e.latlng.lat.toFixed(6);
            document.getElementById('longitude').value = e.latlng.lng.toFixed(6);
        });
    }
}

// Загрузка идей при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initMapPicker();
    
    // Если есть функция загрузки идей, вызываем её
    if (typeof loadIdeas === 'function') {
        loadIdeas();
    }
});