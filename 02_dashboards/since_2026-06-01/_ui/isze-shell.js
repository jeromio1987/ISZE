(function () {
  if (new URLSearchParams(location.search).get('embed') === '1') return;
  if (document.getElementById('isze-editorial-chrome')) return;

  var path = (location.pathname || '').split('/').pop() || 'index.html';
  var isHub = path === 'PROJECT_HUB.html';
  var isPropertiq = path.indexOf('PROPERTIQ') === 0;
  var isMaster = path === 'MASTER_DASHBOARD.html';

  var links = [
    { href: 'PROJECT_HUB.html', label: 'Hub', match: ['PROJECT_HUB.html'] },
    { href: 'MASTER_DASHBOARD.html', label: 'Mission Control', match: ['MASTER_DASHBOARD.html'] },
    { href: 'AI_Operations_Explorer.html', label: 'AI Ops', match: ['AI_Operations_Explorer.html'] },
    { href: 'PROPERTIQ.html', label: 'PROPERTIQ', match: ['PROPERTIQ.html', 'v01_split_hero.html'] },
    { href: 'AIM_Dashboard_CY2025.html', label: 'AIM', match: ['AIM_Dashboard_CY2025.html'] },
    { href: 'ISZE_Competitiveness_Dashboard.html', label: 'Pricing', match: ['ISZE_Competitiveness_Dashboard.html'] }
  ];

  var chrome = document.createElement('header');
  chrome.id = 'isze-editorial-chrome';

  var logo = document.createElement('a');
  logo.className = 'ed-logo';
  logo.href = 'PROJECT_HUB.html';
  logo.innerHTML = '<span>ISZE</span> Intelligence';

  var nav = document.createElement('nav');
  links.forEach(function (l) {
    var a = document.createElement('a');
    a.href = l.href;
    a.textContent = l.label;
    if (l.match.indexOf(path) !== -1) a.className = 'active';
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

  if (isHub || isPropertiq) {
    document.body.style.paddingTop = '48px';
  }
})();
