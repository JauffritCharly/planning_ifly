/* ── Config ── */
const RESERVE_URL = 'https://www.iflyfrance.com/bons-cadeaux/utiliser-un-bon-ifly/';

const DAY_NAMES   = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
const MONTH_NAMES = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];

const TIME_GROUPS = {
  'Matin (10h–13h)':       [10, 11, 12],
  'Après-midi (13h–18h)':  [13, 14, 15, 16, 17],
  'Soirée (18h–23h)':      [18, 19, 20, 21, 22]
};

/* ── State ── */
let allDays          = [];
let currentWeekStart = null;
let activeDayIndex   = 0;

/* ── Date helpers ── */
function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = (day === 0) ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function toKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function getWeekDays(monday) {
  return Array.from({ length: 7 }, (_, i) => addDays(monday, i));
}

/* ── Data helpers ── */
function getSlotsForDate(dateKey) {
  const found = allDays.find(d => d.date === dateKey);
  return found ? found.time_slots : [];
}

function groupSlotsByPeriod(slots) {
  const grouped = {};
  for (const [label, hours] of Object.entries(TIME_GROUPS)) {
    const matching = slots.filter(t => {
      const h = parseInt(t.split(':')[0], 10);
      return hours.includes(h);
    });
    if (matching.length) grouped[label] = matching;
  }
  return grouped;
}

/* ── Render ── */
function formatWeekLabel(monday) {
  const sunday = addDays(monday, 6);
  const sm   = monday.getDate();
  const em   = sunday.getDate();
  const smth = MONTH_NAMES[monday.getMonth()];
  const emth = MONTH_NAMES[sunday.getMonth()];
  if (monday.getMonth() === sunday.getMonth()) {
    return `${sm} – ${em} ${emth} ${sunday.getFullYear()}`;
  }
  return `${sm} ${smth} – ${em} ${emth} ${sunday.getFullYear()}`;
}

function renderWeek() {
  const days  = getWeekDays(currentWeekStart);
  const today = new Date(); today.setHours(0, 0, 0, 0);

  // ── Days strip ──
  const strip = document.getElementById('daysStrip');
  strip.innerHTML = '';

  days.forEach((day, i) => {
    const key    = toKey(day);
    const slots  = getSlotsForDate(key);
    const isToday = day.getTime() === today.getTime();

    const tab = document.createElement('div');
    tab.className = [
      'day-tab',
      isToday         ? 'today'     : '',
      slots.length    ? 'has-slots' : '',
      i === activeDayIndex ? 'active' : ''
    ].filter(Boolean).join(' ');

    tab.innerHTML = `
      <div class="day-name">${DAY_NAMES[day.getDay()]}</div>
      <div class="day-num">${day.getDate()}</div>
      <div class="day-dot"></div>
    `;

    tab.addEventListener('click', () => {
      activeDayIndex = i;
      renderWeek();
    });

    strip.appendChild(tab);
  });

  // ── Week label ──
  document.getElementById('weekLabel').textContent = formatWeekLabel(currentWeekStart);

  // ── Prev / Next buttons ──
  const firstDataDate = allDays.length ? new Date(allDays[0].date + 'T00:00:00') : null;
  const lastDataDate  = allDays.length ? new Date(allDays[allDays.length - 1].date + 'T00:00:00') : null;
  const prevMonday = addDays(currentWeekStart, -7);
  const nextMonday = addDays(currentWeekStart, 7);

  document.getElementById('prevWeek').disabled = firstDataDate && prevMonday < getMonday(firstDataDate);
  document.getElementById('nextWeek').disabled = lastDataDate  && nextMonday > getMonday(lastDataDate);

  // ── Slots content ──
  const activeDay    = days[activeDayIndex];
  const activeDayKey = toKey(activeDay);
  const slots        = getSlotsForDate(activeDayKey);
  const content      = document.getElementById('content');

  if (!slots.length) {
    const dayFull = `${DAY_NAMES[activeDay.getDay()]} ${activeDay.getDate()} ${MONTH_NAMES[activeDay.getMonth()]}`;
    content.innerHTML = `
      <div class="no-slots">
        <div class="no-slots-icon">✦</div>
        Aucun créneau disponible<br>le ${dayFull}
      </div>`;
    return;
  }

  const grouped    = groupSlotsByPeriod(slots);
  const totalLabel = slots.length === 1 ? '1 créneau' : `${slots.length} créneaux`;
  const dayFull    = `${DAY_NAMES[activeDay.getDay()]} ${activeDay.getDate()} ${MONTH_NAMES[activeDay.getMonth()]}`;

  let html = `<div class="summary-bar">
    <div class="summary-pill"><strong>${totalLabel}</strong> disponibles le ${dayFull}</div>
  </div>`;

  for (const [label, groupSlots] of Object.entries(grouped)) {
    html += `<div class="time-group">
      <div class="time-group-label">${label}</div>
      <div class="slots-row">`;

    groupSlots.forEach(time => {
      const [h, m] = time.split(':').map(Number);
      const endDate = new Date(0, 0, 0, h, m + 30);
      const endStr  = `${String(endDate.getHours()).padStart(2,'0')}:${String(endDate.getMinutes()).padStart(2,'0')}`;
      html += `<a class="slot" href="${RESERVE_URL}" target="_blank" rel="noopener">
        ${time} – ${endStr}<span class="slot-arrow">↗</span>
      </a>`;
    });

    html += `</div></div>`;
  }

  content.innerHTML = html;
}

/* ── Navigation events ── */
document.getElementById('prevWeek').addEventListener('click', () => {
  currentWeekStart = addDays(currentWeekStart, -7);
  activeDayIndex   = 0;
  renderWeek();
});

document.getElementById('nextWeek').addEventListener('click', () => {
  currentWeekStart = addDays(currentWeekStart, 7);
  activeDayIndex   = 0;
  renderWeek();
});

/* ── Load planning.json ── */
fetch('planning.json?v=' + Date.now())
  .then(r => {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  })
  .then(planning => {
    allDays = planning;

    // Ouvrir sur la semaine du premier créneau dispo (ou aujourd'hui)
    const today     = new Date(); today.setHours(0, 0, 0, 0);
    const firstDate = allDays.length ? new Date(allDays[0].date + 'T00:00:00') : today;
    const startDate = firstDate >= today ? firstDate : today;
    currentWeekStart = getMonday(startDate);

    // Sélectionner le jour actuel s'il est dans la semaine affichée
    const weekDays = getWeekDays(currentWeekStart);
    const todayKey = toKey(today);
    const todayIdx = weekDays.findIndex(d => toKey(d) === todayKey);
    activeDayIndex  = todayIdx >= 0 ? todayIdx : 0;

    renderWeek();
  })
  .catch(err => {
    document.getElementById('content').innerHTML =
      `<div class="error-box">Impossible de charger le planning.<br><small>${err}</small></div>`;
  });
