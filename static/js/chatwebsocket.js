  class ChatWebSocket {
      constructor() {
          this.socket = null;
          this.currentUser = null;
          this.activeConversation = null;
          this.isTempUser = false;
          this.connect();
      }
      connect() {
          try {
              const userElement = document.getElementById('user-data');
              if (userElement) {
                  this.currentUser = JSON.parse(userElement.textContent);
              } else {
                  this.currentUser = { id: 0, username: 'Anonymous' };
                  this.isTempUser = true;
                  console.warn('No user data found - using anonymous session');
              }
              const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
              this.socket = new WebSocket(`${wsScheme}${window.location.host}/ws/home/`);
              this.socket.onopen = () => console.log('WebSocket connection established');
              this.socket.onmessage = (e) => {
                  const data = JSON.parse(e.data);
                  this.handleMessage(data);
              };
              this.socket.onclose = () => {
                  console.log('WebSocket connection closed');
                  setTimeout(() => this.connect(), 5000);
              };
              this.socket.onerror = (err) => console.error('WebSocket error:', err);
          } catch (error) {
              console.error('WebSocket initialization error:', error);
          }
      }
      handleMessage(data) {
          switch (data.type) {
              case 'chat_message':
                  this.displayNewMessage(data.message);
                  window.__chatUI?.storeIncoming(data.message);
                  break;
              case 'notification':
                  this.showNotification(data.message);
                  break;
              case 'typing':
                  this.updateTypingIndicator(data);
                  break;
              case 'reaction':
                  this.updateMessageReaction(data);
                  break;
          }
      }
      sendMessage(content, conversationId) {
          if (this.socket?.readyState === WebSocket.OPEN) {
              this.socket.send(JSON.stringify({
                  type: 'chat_message',
                  conversation_id: conversationId,
                  content: content
              }));
          }
      }
      sendTypingIndicator(conversationId, isTyping) {
          if (this.socket?.readyState === WebSocket.OPEN) {
              this.socket.send(JSON.stringify({
                  type: 'typing',
                  conversation_id: conversationId,
                  is_typing: isTyping
              }));
          }
      }
      sendReaction(messageId, emoji) {
          if (this.socket?.readyState === WebSocket.OPEN) {
              this.socket.send(JSON.stringify({
                  type: 'reaction',
                  message_id: messageId,
                  emoji: emoji
              }));
          }
      }
      displayNewMessage(message) {
        if (String(message.sender_id) === String(this.currentUser.id)) {
          return; // Skip rendering own messages
        }

          const isMine = String(message.sender_id) === String(this.currentUser.id);
          window.__chatUI?.renderMessage({
            id: message.id,
            author: isMine ? "You" : message.sender_name || "Student",
            side: isMine ? "sent" : "received",
            content: message.content,
            ts: message.timestamp,
            attachments: []
          }, false);
          if (!isMine) window.__chatUI?.playNotificationSound?.();
      }
      showNotification(msg) {
          const el = document.querySelector('.notification-alert');
          if (!el) return;
          el.querySelector('.notification-message').textContent = msg;
          el.style.display = 'block';
          setTimeout(() => {el.style.opacity = '0';setTimeout(() => {
          el.style.display = 'none';
                }, 300);
            }, 3000);
          }
      updateTypingIndicator(data) {
          const typingElement = document.getElementById('typing-indicator');
          if (typingElement) typingElement.textContent = data.is_typing ? `${data.user_name} is typing...` : '';
      }
      updateMessageReaction(data) {
          // no-op here; UI can add if needed
      }
  }
  

//   <!-- ========= Chat logic (using your ChatWebSocket logic, embedded here 1:1 so we don't modify backend files) ========= --

//   <!-- ========= UI wiring: sidebar, draggable divider, graffiti, session history, files ========= -->
  
    (function(){
      /* Globals */
      const chat = new ChatWebSocket();          // use the same logic
      window.__chat = chat;
      const convData = document.getElementById('conversation-data');
      if (convData) {
        try {
          const parsed = JSON.parse(convData.textContent);
          chat.activeConversation = parsed.conversation_id;
          console.log('[DEBUG] Active conversation set to:', chat.activeConversation);
        } catch (e) { console.error('[ERROR] parse conversation-data:', e); }
      }

      /* DOM refs */
      const meNameEl = document.getElementById('current-username');
      const msgArea  = document.getElementById('messages');
      const typingEl = document.getElementById('typing-indicator');
      const sendBtn  = document.getElementById('send-button');
      const msgInput = document.getElementById('message-text');
      const emojiBtn = document.getElementById('emoji-trigger');
      const emojiBox = document.getElementById('emoji-container');
      const attachBtn= document.getElementById('attach-btn');
      const fileIn   = document.getElementById('file-input');
      const userList = document.getElementById('user-list');
      const filterIn = document.getElementById('user-filter');
      const divider  = document.getElementById('divider');
      const targetNameEl = document.getElementById('active-contact-name');
      const targetStatusEl = document.getElementById('active-contact-status');
      const mobileMenuBtn = document.querySelector('.mobile-menu-btn');

      /* Show current username as the RANDOM NUMBER (per request) */
      try {
        const u = JSON.parse(document.getElementById('user-data').textContent);
        meNameEl.textContent = String(u.id); // show the number
      } catch { /* noop */ }

      /* Emoji picker (simple) */
      const emojis = ['😀','😂','😍','👍','❤️','🔥','🎉','🤔','📚','🎓','✏️','📎'];
      emojis.forEach(e => {
        const s = document.createElement('span');
        s.textContent = e; s.style.cursor='pointer'; s.style.fontSize='20px'; s.style.margin='5px';
        s.onclick = () => { msgInput.value += e; msgInput.focus(); };
        emojiBox.appendChild(s);
      });
      emojiBtn.onclick = () => emojiBox.classList.toggle('show');

      /* Sidebar: random users + online status (session-persistent) */
      const CONTACTS_KEY = 'campus_chat_contacts_v1';
      const HISTORY_KEY  = 'campus_chat_history_v1';
      const rng = (min,max)=> Math.floor(Math.random()*(max-min+1))+min;

      function initContacts(){
        const cached = sessionStorage.getItem(CONTACTS_KEY);
        if (cached) return JSON.parse(cached);
        const sample = Array.from({length: 8}).map((_ ,i)=>({
          id: rng(1000,9999),
          name: `Student ${rng(100,999)}`,
          online: Math.random() > 0.4,
          last: 'Tap to open chat'
        }));

        if (window.innerWidth <= 768) {
          userList.classList.remove('visible');
        }
        sessionStorage.setItem(CONTACTS_KEY, JSON.stringify(sample));
        return sample;
      }
      let CONTACTS = initContacts();
      let ACTIVE_CONTACT = null;

      function saveContacts(){ sessionStorage.setItem(CONTACTS_KEY, JSON.stringify(CONTACTS)); }

      /* Message history per contact (session) */
      function getHistory(){
        const raw = sessionStorage.getItem(HISTORY_KEY);
        return raw ? JSON.parse(raw) : {};
      }
      function setHistory(map){ sessionStorage.setItem(HISTORY_KEY, JSON.stringify(map)); }
      function pushToHistory(contactId, msg){
        const map = getHistory();
        map[contactId] = map[contactId] || [];
        map[contactId].push(msg);
        setHistory(map);
      }
      function loadHistory(contactId){ const map = getHistory(); return map[contactId] || []; }

      /* Render contacts */
      function renderContacts(list=CONTACTS){
        // Keep search + header (first child is search)
        const siblings = Array.from(userList.querySelectorAll('.user-item'));
        siblings.forEach(s => s.remove());
        list.forEach(c=>{
          const item = document.createElement('div');
          item.className = 'user-item';
          item.dataset.id = c.id;
          item.innerHTML = `
            <div class="avatar">
              ${String(c.name).split(' ').pop().slice(-2)}
              <span class="status-dot ${c.online ? 'status-online':'status-offline'}"></span>
            </div>
            <div class="user-meta">
              <div class="user-name">${c.name}</div>
              <div class="user-last" id="last-${c.id}">${c.last || ''}</div>
            </div>`;
          item.onclick = ()=>selectContact(c.id);
          userList.appendChild(item);
        });
        // Highlight active
        highlightActive();
      }
      function highlightActive(){
        userList.querySelectorAll('.user-item').forEach(el=>{
          if (ACTIVE_CONTACT && String(el.dataset.id)===String(ACTIVE_CONTACT.id)) el.classList.add('active');
          else el.classList.remove('active');
        });
      }

      /* Select contact */
      function selectContact(id){
        ACTIVE_CONTACT = CONTACTS.find(c=> String(c.id)===String(id));
        highlightActive();
        targetNameEl.textContent = ACTIVE_CONTACT.name;
        targetStatusEl.textContent = ACTIVE_CONTACT.online ? 'Online' : 'Offline';
        // Load history to UI
        msgArea.innerHTML = '';
        const hist = loadHistory(ACTIVE_CONTACT.id);
        hist.forEach(m => renderMessage(m, true));
        // Scroll down
        msgArea.scrollTop = msgArea.scrollHeight;
      }

      /* Messages rendering */
      function renderMessage(m, skipStore){
        const wrap = document.createElement('div');
        wrap.className = `message ${m.side}`;
        const time = new Date(m.ts || Date.now()).toLocaleTimeString();
        wrap.innerHTML = `
          ${m.author ? `<div class="author">${m.author}</div>`:''}
          <div class="content">${escapeHtml(m.content || '')}</div>
          ${Array.isArray(m.attachments) && m.attachments.length ? renderAttachmentsHTML(m.attachments):''}
          <div class="meta"><span>${time}</span></div>
        `;
        msgArea.appendChild(wrap);
        if (!skipStore && ACTIVE_CONTACT) {
          pushToHistory(ACTIVE_CONTACT.id, m);
          updateLastPreview(ACTIVE_CONTACT.id, m);
        }
        msgArea.scrollTop = msgArea.scrollHeight;
      }
      function renderAttachmentsHTML(files){
        const html = files.map(f=>{
          if (f.type.startsWith('image/')) {
            return `<img class="attachment" src="${f.url}" alt="${f.name}">`;
          }
          return `<span class="file-pill">📄 <a href="${f.url}" target="_blank">${f.name}</a></span>`;
        }).join(' ');
        return `<div class="attachments">${html}</div>`;
      }
      function updateLastPreview(contactId, m){
        const el = document.getElementById(`last-${contactId}`);
        if (el) {
          const text = m.attachments?.length ? (m.attachments[0].type.startsWith('image/')?'[Photo]':'[File]') : (m.content || '');
          el.textContent = text;
          const c = CONTACTS.find(x=>String(x.id)===String(contactId));
          if (c){ c.last = text; saveContacts(); }
        }
      }
      function escapeHtml(str){
        return String(str)
          .replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')
          .replaceAll('"','&quot;').replaceAll("'",'&#039;');
      }

      /* Expose for ChatWebSocket on incoming */
      window.__chatUI = {
        renderMessage,
        playNotificationSound(){
          const audio = new Audio('{% static "sounds/Bell-notification-933.wav" %}');
          audio.play().catch(()=>{});
        },
        storeIncoming(msg){
          // If a contact with same sender_id exists, store under them; else store under the active contact
          const target = CONTACTS.find(c => String(c.id) === String(msg.sender_id)) || ACTIVE_CONTACT;
          if (!target) return;
          const payload = {
            id: msg.id,
            author: msg.sender_name || 'Student',
            side: String(msg.sender_id) === String(chat.currentUser?.id) ? 'sent' : 'received',
            content: msg.content, ts: msg.timestamp, attachments: []
          };
          pushToHistory(target.id, payload);
          if (ACTIVE_CONTACT && String(ACTIVE_CONTACT.id) === String(target.id)) {
            // Already rendered in displayNewMessage; just update preview
            updateLastPreview(target.id, payload);
          }
        }
      };

      /* Send message */
      let typingTimeout;
      msgInput.addEventListener('input', ()=>{
        if (chat.activeConversation){
          chat.sendTypingIndicator(chat.activeConversation, true);
          clearTimeout(typingTimeout);
          typingTimeout = setTimeout(()=> chat.sendTypingIndicator(chat.activeConversation, false), 1200);
        }
      });
      sendBtn.addEventListener('click', ()=> doSend());
      msgInput.addEventListener('keydown', (e)=>{
        if (e.key === 'Enter') { e.preventDefault(); doSend(); }
      });

      function doSend(){
        const txt = msgInput.value.trim();
        if (!ACTIVE_CONTACT) { toast('Pick someone to chat with'); return; }
        if (!txt && !fileIn.files.length) return;
        // 1) Text via WS + UI
        if (txt) {
          if (chat.activeConversation) chat.sendMessage(txt, chat.activeConversation);
          renderMessage({ author:'You', side:'sent', content:txt, ts:Date.now(), attachments:[] }, false);
          msgInput.value = '';
          chat.sendTypingIndicator(chat.activeConversation, false);
        }
        // 2) Attachments (frontend only) - create object URLs
        if (fileIn.files.length){
          const atts = Array.from(fileIn.files).map(f=>{
            const url = URL.createObjectURL(f);
            return { name:f.name, url, type:f.type || 'application/octet-stream' };
          });
          renderMessage({ author:'You', side:'sent', content:'', ts:Date.now(), attachments:atts }, false);
          // Optionally notify others textually (since backend file upload is not implemented)
          if (chat.activeConversation) chat.sendMessage(`[Sent ${atts.length} attachment(s)]`, chat.activeConversation);
          fileIn.value = '';
        }
      }

      /* Attachment button */
      attachBtn.onclick = ()=> fileIn.click();

      /* Search filter */
      filterIn.addEventListener('input', ()=>{
        const q = filterIn.value.toLowerCase();
        const filtered = CONTACTS.filter(c=> c.name.toLowerCase().includes(q) || String(c.id).includes(q));
        renderContacts(filtered);
      });

      /* Draggable divider logic */
      (function dividerDrag(){
        let dragging = false;
        let startX = 0;
        let startWidth = 0;
        const MIN = 160, MAX = 360;
        const leftPane = document.querySelector('.user-list');
        divider.addEventListener('mousedown', (e)=>{
          dragging = true; divider.classList.add('dragging');
          startX = e.clientX; startWidth = leftPane.getBoundingClientRect().width;
          document.body.style.userSelect = 'none';
        });
        window.addEventListener('mousemove', (e)=>{
          if (!dragging) return;
          const dx = e.clientX - startX;
          let w = Math.max(MIN, Math.min(MAX, startWidth + dx));
          leftPane.style.width = w + 'px';
        });
        window.addEventListener('mouseup', ()=>{
          if (!dragging) return;
          dragging = false; divider.classList.remove('dragging');
          document.body.style.userSelect = '';
        });
      })();

      /* Toast helper using existing .notification-alert box */
      function toast(msg){
        const box = document.querySelector('.notification-alert');
        if (!box) return;
        box.querySelector('.notification-message').textContent = msg;
        box.style.display = 'block';
        setTimeout(()=> box.style.display='none', 2500);
        chat.showNotification(msg);
      }

      /* Seed UI */
      renderContacts();
      // Auto-select first contact initially
      const first = CONTACTS[0]; if (first) selectContact(first.id);

      mobileMenuBtn.addEventListener('click', () => {
        userList.classList.toggle('visible');
      });

      // Auto-hide typing after inactivity
      let typingHideTimer=null;
      const originalUpdateTyping = chat.updateTypingIndicator.bind(chat);
      chat.updateTypingIndicator = (data)=>{
        originalUpdateTyping(data);
        clearTimeout(typingHideTimer);
        typingHideTimer = setTimeout(()=> { if (typingEl) typingEl.textContent=''; }, 3000);
      };

    })();
  