const CONFIG = {
  WS_URL: 'ws://192.168.1.39:9000', // Cambiar por la IP de la otra PC, ej: ws://192.168.1.50:9000
  MODELS_URI: '/models',
  DETECTION_INTERVAL_MS: 50,
  LOG_INTERVAL_MS: 100,
  CSV_COLUMNS: ['timestamp', 'neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised', 'dominant']
};

const video = document.getElementById('video');
const downloadBtn = document.getElementById('downloadCsvBtn');

let ws = null;
let wsOpen = false;
let sentREADY = false;

let armedT0 = null;   // t0 anunciado por ARM (epoch ms)
let startT0 = null;   // t0 efectivo de START (epoch ms)
let started = false;  // hasta START no guardamos
let sujetoId = null;  // numero de sujeto (viene de META)
let csvFilename = null; // nombre esperado del CSV (opcional, viene por WS)

const emotionLogs = [];

function dominantExpression(expressions) {
  const sorted = Object.entries(expressions || {}).sort((a, b) => b[1] - a[1]);
  return sorted[0]?.[0] || null;
}

function buildCsvTextFixed() {
  if (!emotionLogs.length) return '';
  const header = CONFIG.CSV_COLUMNS.join(',');
  const rows = emotionLogs.map(r => CONFIG.CSV_COLUMNS.map(k => r[k]).join(',')).join('\n');
  return header + '\n' + rows;
}

// ===== Descarga local + backups (redundancia) =====
function downloadTextFile(text, filename, mime = 'text/csv;charset=utf-8') {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();

  setTimeout(() => {
    URL.revokeObjectURL(url);
    a.remove();
  }, 0);
}

function safeFilenamePart(x) {
  return String(x ?? '').trim().replace(/[^\w\-]+/g, '_').slice(0, 60) || 'anon';
}

function saveCsvBackupLocal(csvText, sujetoId) {
  try {
    const key = `emotions_csv_${safeFilenamePart(sujetoId)}_${Date.now()}`;
    localStorage.setItem(key, csvText);
    console.log('[CSV] Backup guardado en localStorage:', key);
  } catch (e) {
    console.warn('[CSV] No se pudo guardar backup en localStorage', e);
  }
}

function makeCsvFilename() {
  if (csvFilename) return String(csvFilename);
  return `emociones_sujeto${safeFilenamePart(sujetoId)}.csv`;
}

function updateDownloadButtonState() {
  if (!downloadBtn) return;
  downloadBtn.disabled = emotionLogs.length === 0;
}

// ===== Botón: descarga manual =====
if (downloadBtn) {
  downloadBtn.addEventListener('click', () => {
    const csv = buildCsvTextFixed();
    if (!csv) {
      alert('No hay datos de emociones para descargar.');
      return;
    }
    downloadTextFile(csv, makeCsvFilename());
    saveCsvBackupLocal(csv, sujetoId);
    console.log('[CSV] Descarga manual realizada');
  });
}

// ===== WebSocket con reconexión simple =====
let reconnectAttempts = 0;
function connectWS() {
  ws = new WebSocket(CONFIG.WS_URL);
  ws.onopen = () => {
    wsOpen = true;
    reconnectAttempts = 0;
    console.log('[SYNC] Conectado al servidor');
    ws.send(JSON.stringify({ type: 'HELLO', role: 'web' }));
    maybeSendREADY();
  };

  ws.onmessage = (ev) => {
    let msg = {};
    try { msg = JSON.parse(ev.data || '{}'); } catch (e) {}

    if (msg.type === 'ACK') {
      if (typeof msg.sujeto_id !== 'undefined' && msg.sujeto_id !== null) {
        sujetoId = msg.sujeto_id;
        console.log('[SYNC] ACK con sujeto_id', sujetoId);
      }
      if (msg.csv_filename) {
        csvFilename = msg.csv_filename;
      }
      return;
    }

    if (msg.type === 'META') {
      sujetoId = msg.sujeto_id || null;
      csvFilename = msg.csv_filename || csvFilename;
      console.log('[SYNC] META recibido -> sujeto', sujetoId);
      return;
    }

    if (msg.type === 'ARM' && typeof msg.t0 === 'number') {
      armedT0 = msg.t0;
      console.log('[SYNC] ARM recibido', new Date(armedT0).toISOString());
      return;
    }

    if (msg.type === 'START' && typeof msg.t0 === 'number') {
      startT0 = msg.t0;
      started = true;
      console.log('[SYNC] START recibido', new Date(startT0).toISOString());
      if (video.paused) video.play().catch(() => {});
      return;
    }

    if (msg.type === 'FIN') {
      csvFilename = msg.csv_filename || csvFilename;
      console.log('[SYNC] FIN recibido → enviando CSV al servidor (y habilitando descarga)');

      const csv = buildCsvTextFixed();
      if (!csv) {
        console.warn('[CSV] No hay datos para exportar');
        return;
      }

      // Enviar al servidor (si se puede)
      if (wsOpen) {
        try {
          ws.send(JSON.stringify({ type: 'CSV_DATA', sujeto_id: sujetoId, csv_text: csv }));
          console.log('[SYNC] CSV enviado al servidor');
        } catch (e) {
          console.warn('[SYNC] Falló el envío por WS', e);
        }
      } else {
        console.warn('[SYNC] WS no está abierto; no se pudo enviar CSV al servidor');
      }

      // No forzamos descarga automática; queda para el botón
      updateDownloadButtonState();
      return;
    }
  };

  ws.onclose = () => {
    wsOpen = false;
    console.warn('[SYNC] WS cerrado');
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts++), 10000);
    setTimeout(connectWS, delay);
  };

  ws.onerror = (e) => {
    console.warn('[SYNC] WS error:', e);
  };
}

// ===== Carga de modelos FaceAPI =====
let modelsLoaded = false;
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri(CONFIG.MODELS_URI),
  faceapi.nets.faceExpressionNet.loadFromUri(CONFIG.MODELS_URI)
]).then(() => {
  modelsLoaded = true;
  console.log('[FaceAPI] Modelos cargados');
  startVideo();
  maybeSendREADY();
});

// ===== Video stream =====
let streamReady = false;
function startVideo() {
  const constraints = { video: {} };
  const onStream = (stream) => {
    video.srcObject = stream;
    streamReady = true;
    maybeSendREADY();
  };
  const onErr = (err) => console.error(err);

  if (navigator.mediaDevices?.getUserMedia) {
    navigator.mediaDevices.getUserMedia(constraints).then(onStream).catch(onErr);
  } else {
    navigator.getUserMedia(constraints, onStream, onErr);
  }
}

function maybeSendREADY() {
  if (!wsOpen || sentREADY || !modelsLoaded || !streamReady) return;
  if (!video) return;

  // Nota: a veces videoWidth/videoHeight están en 0 hasta que arranca el stream;
  // por eso también tenemos loadedmetadata abajo.
  if (video.readyState < 1 || !(video.videoWidth && video.videoHeight)) return;

  sentREADY = true;
  ws.send(JSON.stringify({ type: 'READY' }));
  console.log('[SYNC] READY enviado');
}

video.addEventListener('loadedmetadata', () => {
  streamReady = true;
  maybeSendREADY();
});

// ===== Loop principal de detección =====
let detectionLoopStarted = false;

video.addEventListener('play', () => {
  maybeSendREADY();

  // Evitar múltiples intervals si play se dispara varias veces
  if (detectionLoopStarted) return;
  detectionLoopStarted = true;

  const canvas = faceapi.createCanvasFromMedia(video);
  document.body.append(canvas);

  const syncCanvasSize = () => {
    const width  = video.videoWidth  || video.width;
    const height = video.videoHeight || video.height;
    canvas.width = width;
    canvas.height = height;
    faceapi.matchDimensions(canvas, { width, height });
  };

  syncCanvasSize();
  window.addEventListener('resize', syncCanvasSize);

  // Detección
  let lastLogMs = 0;

  setInterval(async () => {
    const detection = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceExpressions();

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!detection) return;

    const displaySize = { width: canvas.width, height: canvas.height };
    const resized = faceapi.resizeResults(detection, displaySize);
    faceapi.draw.drawDetections(canvas, resized);
    faceapi.draw.drawFaceExpressions(canvas, resized);

    if (!started || !startT0) return;

    const now = Date.now();
    if (now - lastLogMs < CONFIG.LOG_INTERVAL_MS) return;
    lastLogMs = now;

    // Cronómetro mm:ss desde START
    const elapsedMs = now - startT0;
    const minutes = Math.floor(elapsedMs / 60000);
    const seconds = Math.floor((elapsedMs % 60000) / 1000);
    const ts = `${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}`;

    const expr = resized.expressions || {};
    emotionLogs.push({
      timestamp: `"${ts}"`, // entre comillas para que Excel no lo reinterprete
      neutral: +(expr.neutral || 0).toFixed(4),
      happy: +(expr.happy || 0).toFixed(4),
      sad: +(expr.sad || 0).toFixed(4),
      angry: +(expr.angry || 0).toFixed(4),
      fearful: +(expr.fearful || 0).toFixed(4),
      disgusted: +(expr.disgusted || 0).toFixed(4),
      surprised: +(expr.surprised || 0).toFixed(4),
      dominant: dominantExpression(expr)
    });

    updateDownloadButtonState();
  }, CONFIG.DETECTION_INTERVAL_MS);
});

connectWS();
