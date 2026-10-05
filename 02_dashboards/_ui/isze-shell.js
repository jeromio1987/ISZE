(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;
  if (document.getElementById('isze-editorial-chrome')) return;

  // Canonical ISZE home = hub/index.html. All hub pages live in hub/.
  // In the grouped source layout a page sits in hub/ or a sibling folder;
  // in the flattened deploy layout everything sits in one folder. Resolve a
  // correct relative prefix for hub links at runtime so file:// and deploy
  // both work.
  var path = (location.pathname || '').replace(/\\/g, '/');
  var file = path.split('/').pop() || 'index.html';
  var dir = path.split('/').slice(0, -1).join('/');
  var folder = (dir.split('/').filter(Boolean).pop() || '').toLowerCase();
  var known = ['hub','sales','fleet','gps','ops','pricing','ids','md_pack','bi','side','_composable','spa_internal'];
  var prefix = (known.indexOf(folder) !== -1 && folder !== 'hub') ? '../hub/' : '';

  var isPropertiq = file.indexOf('PROPERTIQ') === 0;

  var links = [
    { href: prefix + 'index.html', label: 'Home', match: ['index.html'] },
    { href: prefix + 'ISZE_UNIVERSE_BOARD.html', label: 'Where we stand', match: ['ISZE_UNIVERSE_BOARD.html'] },
    { href: prefix + 'ISZE_UNIVERSE_MAP.html', label: 'The whole picture', match: ['ISZE_UNIVERSE_MAP.html'] },
    { href: prefix + 'BI_PACKS.html', label: 'Dashboard Index', match: ['BI_PACKS.html'] },
    { href: prefix + 'MASTER_DASHBOARD.html', label: 'Mission Control', match: ['MASTER_DASHBOARD.html'] },
    { href: prefix + 'PROJECT_HUB.html', label: 'Project Hub', match: ['PROJECT_HUB.html'] },
    { href: prefix + 'AI_Operations_Explorer.html', label: 'AI Ops', match: ['AI_Operations_Explorer.html'] }
  ];

  var chrome = document.createElement('header');
  chrome.id = 'isze-editorial-chrome';

  var logo = document.createElement('a');
  logo.className = 'ed-logo';
  logo.href = prefix + 'index.html';
  logo.innerHTML = '<span>ISZE</span> Intelligence';

  var nav = document.createElement('nav');
  links.forEach(function (l) {
    var a = document.createElement('a');
    a.href = l.href;
    a.textContent = l.label;
    if (l.match.indexOf(file) !== -1) a.className = 'active';
    nav.appendChild(a);
  });

  var page = document.createElement('div');
  page.className = 'ed-page';
  page.textContent = document.title.replace(/^ISZE\s*[—\-|]\s*/i, '').replace(/PROPERTIQ.*/, 'PROPERTIQ');

  chrome.appendChild(logo);
  chrome.appendChild(nav);
  chrome.appendChild(page);
  document.body.insertBefore(chrome, document.body.firstChild);
  document.body.classList.add('isze-editorial');

  if (isPropertiq) {
    document.body.style.paddingTop = '48px';
  }
})();
