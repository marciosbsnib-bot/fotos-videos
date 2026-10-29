const App = (() => {
  let infoTela, canvas;

  document.addEventListener('DOMContentLoaded', () => {
    infoTela = document.getElementById('info-tela');
    canvas = document.getElementById('emulatorCanvas');
    
    EmulatorCore.init(canvas);
  });

  async function carregarJogo(nomeArquivoZip, nomeJogo) {
    infoTela.style.display = 'block';
    canvas.style.display = 'none';
    infoTela.innerText = `A descarregar ${nomeJogo}...`;

    const caminhoZip = `roms/${nomeArquivoZip}`;

    try {
      const response = await fetch(caminhoZip);
      if (!response.ok) throw new Error(`Ficheiro ${nomeArquivoZip} não encontrado em roms/`);
      
      const zipBuffer = await response.arrayBuffer();
      infoTela.innerText = `A extrair ROM...`;

      const zip = new JSZip();
      const zipContent = await zip.loadAsync(zipBuffer);

      let romObject = null;
      for (let filename in zipContent.files) {
        if (filename.endsWith('.a26') || filename.endsWith('.bin')) {
          romObject = zipContent.files[filename];
          break;
        }
      }

      if (!romObject) {
        throw new Error("Nenhum ficheiro de ROM válido encontrado no ZIP!");
      }

      const romBuffer = await romObject.async("arraybuffer");

      infoTela.style.display = 'none';
      canvas.style.display = 'block';

      EmulatorCore.loadAndRun(romBuffer);

    } catch (err) {
      infoTela.innerText = `Erro: ${err.message}`;
      console.error("[Erro no App]", err);
    }
  }

  return {
    carregarJogo
  };
})();