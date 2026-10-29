const EmulatorCore = (() => {
  let canvasElement;
  let emulatorInstance = null;

  function init(canvas) {
    canvasElement = canvas;
    console.log("Core do Emulador inicializado.");
  }

  async function loadAndRun(romBuffer) {
    console.log("A injetar ROM no motor... Tamanho:", romBuffer.byteLength, "bytes");

    try {
      const romUint8Array = new Uint8Array(romBuffer);

      // Se já houver um jogo rodando, tenta parar
      if (emulatorInstance && typeof emulatorInstance.stop === 'function') {
        emulatorInstance.stop();
      }

      // Procura por qualquer objeto global que o script da CDN tenha criado (como Javatari, JAVATARI, etc.)
      const JavatariEngine = window.Javatari || window.JavatariApp || window.Atari || (typeof Javatari !== 'undefined' ? Javatari : null);

      if (!JavatariEngine) {
        // Se a classe exata não veio no escopo global, vamos usar o construtor padrão ou injetar via estrutura interna
        console.warn("Objeto global direto não encontrado, tentando inicialização alternativa...");
      }

      // Inicializa o player passando o canvas e os bytes da ROM
      emulatorInstance = new Javatari({
        canvas: canvasElement,
        rom: romUint8Array,
        audio: true,
        autoStart: true
      });

      console.log("Jogo iniciado com sucesso!");

    } catch (err) {
      console.error("Erro ao iniciar o motor:", err);
      mostrarErroNoCanvas("Erro: " + err.message);
    }
  }

  function mostrarErroNoCanvas(mensagem) {
    const ctx = canvasElement.getContext('2d');
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, canvasElement.width, canvasElement.height);
    ctx.fillStyle = "#ff4444";
    ctx.font = "12px sans-serif";
    ctx.fillText(mensagem, 10, 96);
  }

  return {
    init,
    loadAndRun
  };
})();