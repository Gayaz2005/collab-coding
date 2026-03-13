// Состояние приложения
let currentRoom = null;
let editor = null;
let saveTimeout = null;

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initEditor();
    loadRooms();
    setInterval(loadRooms, 5000);
});

// Инициализация Monaco Editor
function initEditor() {
    require.config({ paths: { vs: '/static/monaco/min/vs' } });
    
    require(['vs/editor/editor.main'], function() {
        editor = monaco.editor.create(document.getElementById('editor'), {
            value: '',
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            fontSize: 14,
            minimap: { enabled: false },
            quickSuggestions: {
                other: true,
                comments: false,
                strings: true
            },
            suggestOnTriggerCharacters: true,
            acceptSuggestionOnEnter: 'on',
            tabCompletion: 'on',
            wordBasedSuggestions: true,
            parameterHints: {
                enabled: true
            },
            snippetSuggestions: 'inline'
        });
        
        editor.onDidChangeModelContent(() => {
            if (currentRoom) {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(saveCode, 30000);
            }
        });
    });
}

// Загрузка списка комнат
async function loadRooms() {
    try {
        const response = await fetch('/rooms');
        const rooms = await response.json();
        displayRooms(rooms);
    } catch (error) {
        showNotification('Ошибка загрузки комнат', 'error');
    }
}

// Отображение списка комнат
function displayRooms(rooms) {
    const container = document.getElementById('roomsContainer');
    
    if (rooms.length === 0) {
        container.innerHTML = '<p class="no-rooms">Нет активных комнат</p>';
        return;
    }
    
    container.innerHTML = rooms.map(room => `
        <div class="room-item" onclick="joinRoom('${room.id}', '${room.name}')">
            <div class="room-info">
                <div class="room-name">${room.name}</div>
                <div class="room-meta">
                    ID: ${room.id.slice(0, 8)}... | 
                    Язык: ${room.language} |
                    Создана: ${new Date(room.created_at).toLocaleString()}
                </div>
            </div>
            <button class="room-join-btn" onclick="event.stopPropagation(); joinRoom('${room.id}', '${room.name}')">
                Войти
            </button>
        </div>
    `).join('');
}

// Создание новой комнаты
async function createRoom() {
    const name = document.getElementById('roomName').value || 'Новая комната';
    
    try {
        const response = await fetch(`/rooms?name=${encodeURIComponent(name)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const room = await response.json();
            showNotification('Комната создана!', 'success');
            loadRooms();
            joinRoom(room.id, room.name);
        }
    } catch (error) {
        showNotification('Ошибка создания комнаты', 'error');
    }
}

// Вход в комнату
async function joinRoom(roomId, roomName) {
    try {
        const response = await fetch(`/rooms/${roomId}`);
        
        if (response.ok) {
            const room = await response.json();
            
            currentRoom = room;
            document.getElementById('currentRoomName').textContent = room.name;
            document.getElementById('mainContent').style.display = 'block';
            
            if (editor) {
                editor.setValue(room.code);
            }
            
            history.pushState({}, '', `?room=${roomId}`);
            showNotification(`Вошел в комнату: ${room.name}`, 'success');
        }
    } catch (error) {
        showNotification('Ошибка входа в комнату', 'error');
    }
}

// Выход из комнаты
function leaveRoom() {
    currentRoom = null;
    document.getElementById('mainContent').style.display = 'none';
    history.pushState({}, '', '/');
}

// Копирование ссылки на комнату
function copyRoomLink() {
    if (!currentRoom) return;
    
    const url = `${window.location.origin}?room=${currentRoom.id}`;
    navigator.clipboard.writeText(url);
    showNotification('Ссылка скопирована!', 'success');
}

// Выполнение кода
async function runCode() {
    if (!currentRoom || !editor) return;
    
    const code = editor.getValue();
    const output = document.getElementById('output');
    output.textContent = 'Выполнение...';
    
    setTimeout(() => {
        output.textContent = 'Функция выполнения кода будет добавлена позже!\n\n' + code;
    }, 1000);
}

// Сохранение кода
async function saveCode() {
    if (!currentRoom || !editor) {
        showNotification('Нет активной комнаты', 'error');
        return;
    }
    
    const code = editor.getValue();
    
    // Показываем что сохраняем
    showNotification('Сохранение...', 'info');
    
    try {
        const response = await fetch(`/rooms/${currentRoom.id}/code?code=${encodeURIComponent(code)}`, {
            method: 'PUT'
        });
        
        if (response.ok) {
            showNotification('Код успешно сохранен!', 'success');
            console.log('Код сохранен в', new Date().toLocaleTimeString());
        } else {
            const error = await response.text();
            console.error('Ошибка сохранения:', error);
            showNotification('Ошибка сохранения кода', 'error');
        }
    } catch (error) {
        console.error('Ошибка запроса:', error);
        showNotification('Ошибка сохранения кода', 'error');
    }
}

// Уведомления
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Проверка URL при загрузке
window.addEventListener('load', () => {
    const params = new URLSearchParams(window.location.search);
    const roomId = params.get('room');
    
    if (roomId) {
        fetch(`/rooms/${roomId}`)
            .then(res => res.json())
            .then(room => joinRoom(room.id, room.name))
            .catch(() => {});
    }
});