let zoom = 1;
function zoomPhoto(factor){
  const img=document.getElementById("photo");
  if(!img)return;
  zoom=Math.min(5,Math.max(.4,zoom*factor));
  img.style.transform=`scale(${zoom})`;
}
function toggleFullscreen(){
  const target=document.querySelector(".viewer-stage");
  if(!target)return;
  if(document.fullscreenElement) document.exitFullscreen();
  else target.requestFullscreen?.();
}

// ===================================
// Funções de Gerenciamento de Mídia
// ===================================

async function alterarPrivacidade(mediaId, novaClassificacao) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  const formData = new FormData();
  formData.append('classification', novaClassificacao);

  try {
    const response = await fetch(`/admin/media/${mediaId}/classification`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    });

    if (!response.ok) {
      alert('Erro ao alterar a privacidade.');
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro de conexão ao alterar a privacidade.');
  }
}

async function eliminarMedia(mediaId) {
  if (!confirm('Tem certeza que deseja excluir esta foto/vídeo?')) {
    return;
  }

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  
  // Cria um FormData e adiciona o token CSRF
  const formData = new FormData();
  if (csrfToken) {
    formData.append('csrf_token', csrfToken);
  }

  try {
    const response = await fetch(`/admin/media/${mediaId}/delete`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    });

    if (response.ok) {
      const card = document.getElementById(`media-card-${mediaId}`);
      if (card) {
        card.remove();
      }
    } else {
      const data = await response.json().catch(() => ({}));
      alert(data.error || data.message || 'Erro ao excluir o arquivo.');
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro de conexão ao excluir o arquivo.');
  }
}

// ===================================
// Alternar Visibilidade do Menu Lateral
// ===================================

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  sidebar.classList.toggle('collapsed');
  
  // Guarda o estado no navegador
  const isCollapsed = sidebar.classList.contains('collapsed');
  localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
}

// Restaura a preferência do menu ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  if (sidebar && localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }
});

// Excluir mídia estando dentro do visualizador e voltar para o álbum
async function eliminarMediaEVoltar(mediaId, albumId) {
  if (!confirm('Tem certeza que deseja excluir esta foto/vídeo?')) {
    return;
  }

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  const formData = new FormData();
  if (csrfToken) {
    formData.append('csrf_token', csrfToken);
  }

  try {
    const response = await fetch(`/admin/media/${mediaId}/delete`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    });

    if (response.ok) {
      window.location.href = `/albums/${albumId}`;
    } else {
      const data = await response.json().catch(() => ({}));
      alert(data.error || data.message || 'Erro ao excluir o arquivo.');
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro de conexão ao excluir o arquivo.');
  }
}

// Controles de Tela Cheia e Zoom
let currentZoom = 1;

function zoomIn() {
  const media = document.getElementById('mediaElement');
  if (media && currentZoom < 3) {
    currentZoom += 0.25;
    media.style.transform = `scale(${currentZoom})`;
  }
}

function zoomOut() {
  const media = document.getElementById('mediaElement');
  if (media && currentZoom > 0.5) {
    currentZoom -= 0.25;
    media.style.transform = `scale(${currentZoom})`;
  }
}

function toggleFullscreen() {
  const media = document.getElementById('mediaElement');
  if (!media) return;

  if (!document.fullscreenElement) {
    media.requestFullscreen().catch(err => alert(`Erro ao entrar em tela cheia: ${err.message}`));
  } else {
    document.exitFullscreen();
  }
}

// ===================================
// Função para Recarregar/Embaralhar o Mural
// ===================================
function recarregarMural() {
    window.location.reload();
}

document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById("mix-container");
    if (!container || typeof muralMediaItems === 'undefined') return;

    if (typeof toggleSidebar === 'function') {
        const sidebar = document.querySelector('.sidebar') || document.querySelector('aside');
        if (sidebar && !sidebar.classList.contains('collapsed') && !sidebar.classList.contains('hide')) {
            toggleSidebar();
        }
    }

    function renderMural() {
        container.querySelectorAll('.mixed-photo').forEach(photo => photo.remove());

        const sidebar = document.querySelector('.sidebar') || document.querySelector('aside');
        const sidebarWidth = (sidebar && (sidebar.classList.contains('collapsed') || sidebar.classList.contains('hide'))) ? 0 : 250;
        const containerWidth = window.innerWidth - sidebarWidth - 200;
        const containerHeight = window.innerHeight - 180;

        muralMediaItems.forEach(function(item) {
            const div = document.createElement('div');
            div.classList.add('mixed-photo');

            const randomX = sidebarWidth + Math.max(30, Math.random() * Math.max(100, containerWidth));
            const randomY = Math.max(90, Math.random() * Math.max(100, containerHeight));
            const randomRotate = Math.floor(Math.random() * 70) - 35;
            const randomZ = Math.floor(Math.random() * muralMediaItems.length);

            div.style.left = randomX + 'px';
            div.style.top = randomY + 'px';
            div.style.transform = `rotate(${randomRotate}deg)`;
            div.style.zIndex = randomZ;

            if (window.userIsAdmin) {
                const deleteForm = document.createElement('form');
                deleteForm.action = `/admin/media/${item.id}/delete`;
                deleteForm.method = 'POST';
                deleteForm.onsubmit = function() {
                    return confirm('Tem certeza que deseja excluir esta mídia?');
                };
                deleteForm.innerHTML = `
                    <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                    <button type="submit" class="mural-admin-delete" title="Excluir mídia">🗑️</button>
                `;
                div.appendChild(deleteForm);
            }

            const wrapper = document.createElement('div');
            wrapper.classList.add('mixed-photo-wrapper');

            const img = document.createElement('img');
            img.alt = "Foto do mural";
            img.loading = "lazy";
            img.decoding = "async";
            img.src = item.url;

            img.onerror = function() {
                if (!img.dataset.fallbackTried) {
                    img.dataset.fallbackTried = "true";
                    img.src = item.fallbackUrl;
                } else {
                    img.onerror = null;
                }
            };

            wrapper.appendChild(img);

            if (item.isVideo) {
                const playOverlay = document.createElement('div');
                playOverlay.classList.add('video-play-overlay');
                wrapper.appendChild(playOverlay);
            }

            wrapper.addEventListener('click', function() {
                openModal(item);
            });

            div.appendChild(wrapper);

            const glassBar = document.createElement('div');
            glassBar.classList.add('mural-glass-bar');

            glassBar.innerHTML = `
                <span title="Visualizações" style="font-size: 11px; color: #ccc;">
                <i class="fa-regular fa-eye"></i> ${item.views}</span>
                <form action="/media/${item.id}/like" method="POST" style="margin:0;">
                    <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                    <button type="submit" class="mural-action-btn ${item.isLiked ? 'active-like' : ''}" title="Curtir">
                    <i class="fa-solid fa-fire"></i>
                    <span class="like-count">${item.likes}</span></button>
                </form>
                <form action="/media/${item.id}/favorite" method="POST" style="margin:0;">
                    <input type="hidden" name="csrf_token" value="${window.csrfToken}">
                    <button type="submit" class="mural-action-btn ${item.isFavorite ? 'active-fav' : ''}" title="Favoritar"><i class="fa-solid fa-heart"></i> <span class="fav-count">${item.favs}</span></button>
                </form>
            `;

            div.appendChild(glassBar);
            container.appendChild(div);
        });
    }

    renderMural();

    const toggleBtn = document.querySelector('#sidebarToggle') || document.querySelector('.toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            setTimeout(renderMural, 300);
        });
    }
});

function openModal(item) {
    const modal = document.getElementById("mediaModal");
    const modalBody = document.getElementById("modalBody");
    modalBody.innerHTML = "";

    if (item.isVideo) {
        const video = document.createElement('video');
        video.src = item.streamUrl;
        video.controls = true;
        video.autoplay = true;
        video.preload = "metadata";
        modalBody.appendChild(video);
    } else {
        const img = document.createElement('img');
        img.src = item.streamUrl;
        img.alt = "Foto ampliada";
        modalBody.appendChild(img);
    }
    modal.style.display = "flex";
}

function closeModal() {
    const modal = document.getElementById("mediaModal");
    const modalBody = document.getElementById("modalBody");
    modal.style.display = "none";
    modalBody.innerHTML = "";
}

window.addEventListener('click', function(event) {
    const modal = document.getElementById("mediaModal");
    if (event.target === modal) {
        closeModal();
    }
});

window.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

document.addEventListener("submit", function(event) {
    const form = event.target;
    
    // Verifica se é uma ação de like, favorito ou exclusão de mídia
    if (form.matches('form[action*="/like"], form[action*="/favorite"], form[action*="/delete"]')) {
        event.preventDefault(); // Bloqueia o recarregamento padrão da página
        
        const formData = new FormData(form);
        const actionUrl = form.action;

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na resposta da rede: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) return;

            const photoCard = form.closest('.mixed-photo') || form.closest('.media-card');

            // Caso seja exclusão, remove o card visualmente da tela
            if (actionUrl.includes('/delete') && photoCard) {
                photoCard.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                photoCard.style.transform = 'scale(0)';
                photoCard.style.opacity = '0';
                setTimeout(() => photoCard.remove(), 300);
                return;
            }

            const btn = form.querySelector('button');
            if (!btn) return;

            // Caso seja Curtida (Like)
            if (actionUrl.includes('/like')) {
                btn.classList.toggle('active-like', data.liked);
                
                const countSpan = btn.querySelector('.like-count') || btn.querySelector('span');
                if (countSpan) {
                    countSpan.textContent = data.likes_count;
                } else {
                    btn.innerHTML = `🤘 ${data.likes_count}`;
                }
            }

            // Caso seja Favorito (Favorite)
            if (actionUrl.includes('/favorite')) {
                btn.classList.toggle('active-fav', data.favorited);
                
                const countSpan = btn.querySelector('.fav-count') || btn.querySelector('span');
                if (countSpan) {
                    countSpan.textContent = data.favs_count;
                } else {
                    btn.innerHTML = `❤️ ${data.favs_count}`;
                }
            }
        })
        .catch(error => console.error('Erro na requisição assíncrona:', error));
    }
});