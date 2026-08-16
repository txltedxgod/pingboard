const $ = id => document.getElementById(id);
let myId = null;
let selectedEmoji = '\ud83d\udc64';

async function api(url, opts = {}) {
    const res = await fetch(url, {
        headers: {'Content-Type': 'application/json'},
        ...opts
    });
    return res.json();
}

async function loadBoard() {
    const members = await api('/api/members');
    const board = $('board');
    board.innerHTML = '';

    members.forEach(m => {
        const card = document.createElement('div');
        card.className = 'member-card';
        card.id = `member-${m.id}`;

        const isMe = m.id === myId;
        const statuses = ['available', 'busy', 'away', 'meeting', 'offline'];

        let controlsHtml = '';
        if (isMe) {
            controlsHtml = `
                <div class="status-controls">
                    ${statuses.map(s =>
                        `<button class="${m.status === s ? 'active' : ''}" onclick="setStatus(${m.id}, '${s}')">${s}</button>`
                    ).join('')}
                </div>
                <input class="msg-input" placeholder="status message..." value="${m.message || ''}" 
                    onchange="setMessage(${m.id}, this.value)">
            `;
        }

        const time = m.updated_at ? new Date(m.updated_at).toLocaleTimeString() : '';

        card.innerHTML = `
            <div class="avatar">${m.avatar}</div>
            <div class="name">${m.name}</div>
            <span class="status-badge status-${m.status}">${m.status}</span>
            ${m.message ? `<div class="message">${m.message}</div>` : ''}
            <div class="updated-time">${time}</div>
            ${controlsHtml}
        `;
        board.appendChild(card);
    });
}

async function setStatus(id, status) {
    const msgInput = document.querySelector(`#member-${id} .msg-input`);
    const message = msgInput ? msgInput.value : '';
    await api(`/api/members/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status, message })
    });
}

async function setMessage(id, message) {
    const card = document.querySelector(`#member-${id}`);
    const activeBtn = card.querySelector('.status-controls button.active');
    const status = activeBtn ? activeBtn.textContent : 'available';
    await api(`/api/members/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status, message })
    });
}

// SSE
function connectSSE() {
    const source = new EventSource('/api/events');
    source.onmessage = (e) => {
        // just reload the board on any event
        loadBoard();
    };
    source.onerror = () => {
        setTimeout(connectSSE, 3000);
    };
}

// Join modal
$('joinBtn').onclick = () => $('joinModal').classList.remove('hidden');
$('cancelJoin').onclick = () => $('joinModal').classList.add('hidden');

document.querySelectorAll('.emoji-opt').forEach(el => {
    el.onclick = () => {
        document.querySelectorAll('.emoji-opt').forEach(e => e.classList.remove('selected'));
        el.classList.add('selected');
        selectedEmoji = el.dataset.emoji;
    };
});

$('confirmJoin').onclick = async () => {
    const name = $('nameInput').value.trim();
    if (!name) return;
    const member = await api('/api/members', {
        method: 'POST',
        body: JSON.stringify({ name, avatar: selectedEmoji })
    });
    myId = member.id;
    $('joinModal').classList.add('hidden');
    $('nameInput').value = '';
    loadBoard();
};

loadBoard();
connectSSE();
