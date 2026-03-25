// Состояние приложения
let currentRoom = null;
let editor = null;
let saveTimeout = null;
let socket = null;

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
            if (currentRoom && socket && socket.readyState === WebSocket.OPEN) {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    const code = editor.getValue();
                    socket.send(code); 
                }, 1000);
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
    
    if (!rooms || rooms.length === 0) {
        container.innerHTML = '<p class="no-rooms">Нет активных комнат</p>';
        return;
    }
    
    container.innerHTML = rooms.map(room => {
        const roomId = room.id || room.uuid;
        if (!roomId) return '';
        return `
            <div class="room-item" onclick="joinRoom('${roomId}', '${room.name}')">
                <div class="room-info">
                    <div class="room-name">${escapeHtml(room.name) || 'Без имени'}</div>
                    <div class="room-meta">
                        ID: ${roomId.slice(0, 8)}... | 
                        Язык: ${room.language || 'python'} |
                        Создана: ${room.created_at ? new Date(room.created_at).toLocaleString() : 'неизвестно'}
                    </div>
                </div>
                <button class="room-join-btn" onclick="event.stopPropagation(); joinRoom('${roomId}', '${room.name}')">
                    Войти
                </button>
            </div>
        `;
    }).join('');
}

// Создание новой комнаты
async function createRoom() {
    const name = document.getElementById('roomName').value || 'Новая комната';
    
    try {
        const response = await fetch(`/rooms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name })
        });
        
        if (response.ok) {
            const room = await response.json();
            showNotification('Комната создана!', 'success');
            loadRooms();
            joinRoom(room.uuid, room.name);
        } else {
            const error = await response.json();
            console.error('Ошибка создания:', error);
            showNotification('Ошибка создания комнаты', 'error');
        }
    } catch (error) {
        console.error('Ошибка запроса:', error);
        showNotification('Ошибка создания комнаты', 'error');
    }
}

// Вход в комнату
async function joinRoom(roomId, roomName) {
    if (!roomId) {
        showNotification('Ошибка: ID комнаты не указан', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/rooms/${roomId}`);
        
        if (response.ok) {
            const room = await response.json();
            
            // Нормализуем объект: добавляем поле id для совместимости
            currentRoom = {
                ...room,
                id: room.uuid  // 👈 добавляем id для обратной совместимости
            };
            
            document.getElementById('currentRoomName').textContent = room.name;
            document.getElementById('mainContent').style.display = 'block';
            
            if (editor) {
                editor.setValue(room.code || '');
            }
            connectWebSocket(roomId);
            history.pushState({}, '', `?room=${roomId}`);
            showNotification(`Вошел в комнату: ${room.name}`, 'success');
        } else {
            const error = await response.json();
            console.error('Ошибка входа:', error);
            showNotification('Комната не найдена', 'error');
        }
    } catch (error) {
        console.error('Ошибка запроса:', error);
        showNotification('Ошибка входа в комнату', 'error');
    }
}

function connectWebSocket(roomId) {
    if (!roomId) {
        console.error('WebSocket: roomId не указан');
        return;
    }
    
    if (socket) {
        socket.close();
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${roomId}`;
    
    console.log('Подключаюсь к WebSocket:', wsUrl);
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('WebSocket подключен');
    };
    
    socket.onmessage = (event) => {
        const code = event.data;
        if (editor && code !== editor.getValue()) {
            editor.setValue(code);
        }
    };
    
    socket.onerror = (error) => {
        console.error('WebSocket ошибка:', error);
        showNotification('Ошибка подключения', 'error');
    };
    
    socket.onclose = () => {
        console.log('WebSocket отключен');
    };
}

// Выход из комнаты
function leaveRoom() {
    if (socket) {
        socket.close();
        socket = null;
    }
    currentRoom = null;
    document.getElementById('mainContent').style.display = 'none';
    history.pushState({}, '', '/');
    
    if (editor) {
        editor.setValue('');
    }
}

// Копирование ссылки на комнату
function copyRoomLink() {
    if (!currentRoom) return;
    
    const roomId = currentRoom.id || currentRoom.uuid;
    const url = `${window.location.origin}?room=${roomId}`;
    navigator.clipboard.writeText(url);
    showNotification('Ссылка скопирована!', 'success');
}

// Выполнение кода
async function runCode() {
    if (!currentRoom || !editor) {
        showNotification('Нет активной комнаты', 'error');
        return;
    }
    
    const roomId = currentRoom.id || currentRoom.uuid;
    const code = editor.getValue();
    const output = document.getElementById('output');
    output.textContent = 'Выполнение...';
    
    try {
        const response = await fetch(`/rooms/${roomId}/run`, {
            method: 'POST',
        });
        
        const result = await response.json();
        
        if (result.error) {
            output.textContent = `Ошибка: ${result.error}`;
        } else if (result.output) {
            output.textContent = result.output;
        } else {
            output.textContent = 'Код выполнен (нет вывода)';
        }
    } catch (error) {
        console.error('Ошибка выполнения:', error);
        output.textContent = 'Ошибка выполнения';
        showNotification('Ошибка выполнения кода', 'error');
    }
}

// Сохранение кода
async function saveCode() {
    if (!currentRoom || !editor) {
        showNotification('Нет активной комнаты', 'error');
        return;
    }
    
    const code = editor.getValue();
    const roomId = currentRoom.id || currentRoom.uuid;
    
    showNotification('Сохранение...', 'info');
    
    try {
        const response = await fetch(`/rooms/${roomId}/code`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code })
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

// Вспомогательная функция для экранирования HTML
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
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
            .then(room => joinRoom(room.uuid, room.name))
            .catch(() => {});
    }
});