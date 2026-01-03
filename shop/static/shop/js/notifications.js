(function(){
  const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const notificationsSocket = new WebSocket(wsScheme + '://' + window.location.host + '/ws/notifications/');

  function updateBadge(increment) {
    const badgeContainer = document.getElementById('notifications-badge');
    if (!badgeContainer) return;
    let current = badgeContainer.querySelector('.badge');
    if (current) {
      let n = parseInt(current.innerText) || 0;
      n = Math.max(0, n + (increment || 1));
      if (n <= 0) current.remove();
      else current.innerText = n;
    } else if (increment > 0) {
      badgeContainer.innerHTML = '<span class="badge bg-warning text-dark ms-2">' + increment + '</span>';
    }
  }

  notificationsSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    // Update badge by +1
    updateBadge(1);

    // Prepend to notifications list if present
    const list = document.getElementById('notifications-list');
    if (list) {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between align-items-start list-group-item-warning';
      li.setAttribute('data-id', data.id || '');
      li.innerHTML = `
        <div>
          <div>${data.verb} ${data.url ? '<a href="'+data.url+'">Voir</a>' : ''}</div>
          <small class="text-muted">${data.created_at || ''}</small>
        </div>
        <div>
          <button class="btn btn-sm btn-outline-secondary mark-read">Marquer lu</button>
        </div>
      `;
      list.insertBefore(li, list.firstChild);
    }

    // Browser notification
    if (window.Notification && Notification.permission === 'granted') {
      new Notification(data.verb || 'Notification', { body: (data.verb || '') });
    }
  };

  notificationsSocket.onclose = function(e){ console.error('Notifications socket closed'); };

  // handle mark-as-read clicks
  document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('mark-read')) {
      const li = e.target.closest('li');
      const nid = li && li.getAttribute('data-id');
      if (!nid) return;
      fetch(`/notifications/mark_read/${nid}/`, { method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken') } })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            li.classList.remove('list-group-item-warning');
            e.target.remove();
            updateBadge(-1);
          }
        });
    }
    if (e.target && e.target.id === 'mark-all-read') {
      fetch('/notifications/mark_all_read/', { method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken') } })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            document.querySelectorAll('#notifications-list .list-group-item-warning').forEach(el => el.classList.remove('list-group-item-warning'));
            document.querySelectorAll('#notifications-list .mark-read').forEach(btn => btn.remove());
            updateBadge(-9999);
          }
        });
    }
  });

  // helper to get cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Ask for permission for browser notification once
  if (window.Notification && Notification.permission !== 'granted') {
    Notification.requestPermission();
  }
})();