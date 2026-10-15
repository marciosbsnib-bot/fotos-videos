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