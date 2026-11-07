// Entrances, the flow clips and scroll-linked screen, and the privacy switches. The page reads fine without it.

const reveal = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    entry.target.classList.add('is-in');
    reveal.unobserve(entry.target);
  }
}, { rootMargin: '0px 0px -12% 0px' });
document.querySelectorAll('.reveal').forEach((el) => reveal.observe(el));

// Third flow: the page's scroll drives the app screen inside the phone, holding still on each note.
const SCREEN_H = 4061, FRAME_SCREEN_H = 2424; // px of the stitched capture and of one phone screen
const STOPS = [0, 520, SCREEN_H - FRAME_SCREEN_H]; // screen scroll offsets the scene rests on
const showcase = document.querySelector('.showcase');
const screen = showcase.querySelector('.showcase-screen');
const notes = [...showcase.querySelectorAll('.note')];
let activeNote = 0;

const smooth = (t) => t * t * (3 - 2 * t);

// Hold 0–20%, move to the next stop over 20–40%, hold, move over 60–80%, hold.
function screenOffset(progress) {
  const segment = Math.min(4, Math.floor(progress * 5));
  if (segment % 2 === 0) return STOPS[segment / 2];
  const from = STOPS[(segment - 1) / 2];
  const to = STOPS[(segment + 1) / 2];
  return from + (to - from) * smooth(progress * 5 - segment);
}

function noteFor(progress) {
  if (progress < 0.3) return 0;
  return progress < 0.7 ? 1 : 2;
}

function setActiveNote(index) {
  if (index === activeNote) return;
  notes[activeNote].classList.remove('is-active');
  notes[index].classList.add('is-active');
  activeNote = index;
}

function updateShowcase() {
  const box = showcase.getBoundingClientRect();
  const progress = Math.min(1, Math.max(0, -box.top / (box.height - innerHeight)));
  const offset = screenOffset(progress);
  screen.style.transform = `translateY(${(-offset / SCREEN_H) * 100}%)`;
  setActiveNote(noteFor(progress));
}

let frameRequested = false;
function onScroll() {
  if (frameRequested) return;
  frameRequested = true;
  requestAnimationFrame(() => { frameRequested = false; updateShowcase(); });
}

const prefersMotion = !matchMedia('(prefers-reduced-motion: reduce)').matches;

if (prefersMotion) {
  document.documentElement.classList.add('pinned');
  new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) addEventListener('scroll', onScroll, { passive: true });
    else removeEventListener('scroll', onScroll);
  }).observe(showcase);
  addEventListener('resize', onScroll);
  updateShowcase();
}

// Flow clips play only while on screen; with reduced motion they stay on their poster.
const clipWatcher = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) entry.target.play().catch(() => {});
    else entry.target.pause();
  }
}, { threshold: 0.4 });
if (prefersMotion) document.querySelectorAll('.flow-video').forEach((video) => clipWatcher.observe(video));

function setTheme(isDark) {
  document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
}

function toggleBand(button) {
  const band = button.closest('.band');
  const isOn = button.getAttribute('aria-checked') !== 'true';
  button.setAttribute('aria-checked', String(isOn));
  band.classList.toggle('is-on', isOn);
  if (band.dataset.band === 'dark') setTheme(isOn);
}

const darkSwitch = document.querySelector('[data-band="dark"] .switch');
if (matchMedia('(prefers-color-scheme: dark)').matches) {
  darkSwitch.setAttribute('aria-checked', 'true');
  darkSwitch.closest('.band').classList.add('is-on');
}
// The local-storage band has no off: Groowl has nowhere else to keep a diary.
document.querySelectorAll('.switch').forEach((button) => {
  button.addEventListener('click', () => {
    if (button.closest('[data-band="local"]')) {
      button.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-6px)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(0)' }], { duration: 280 });
      return;
    }
    toggleBand(button);
  });
});
